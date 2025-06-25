"""Dialog para mostrar recomendaciones de canciones compatibles."""

from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QTableWidget, QTableWidgetItem, QProgressBar, QSplitter,
                               QTextEdit, QHeaderView, QAbstractItemView, QMessageBox,
                               QComboBox, QSpinBox, QGroupBox, QTabWidget, QWidget, QCheckBox)
from PySide6.QtGui import QFont, QIcon
from typing import Dict, List, Optional, Tuple, Any

from services.recommendation_service import get_recommendation_service
from core.dj_transition_analyzer import TransitionAnalysis


class RecommendationWorker(QThread):
    """Worker thread para generar recomendaciones en background."""
    
    recommendations_ready = Signal(list)  # List[Tuple[Dict, TransitionAnalysis]]
    error_occurred = Signal(str)
    progress_updated = Signal(int)
    
    def __init__(self, current_track: Dict, limit: int = 20, min_score: float = 0.4, filters: Optional[Dict] = None):
        super().__init__()
        self.current_track = current_track
        self.limit = limit
        self.min_score = min_score
        self.filters = filters
        self.rec_service = get_recommendation_service()
    
    def run(self):
        """Ejecuta la generación de recomendaciones."""
        try:
            self.progress_updated.emit(25)
            
            # Generar recomendaciones
            recommendations = self.rec_service.get_compatible_tracks(
                self.current_track, 
                self.limit, 
                self.min_score, 
                self.filters
            )
            
            self.progress_updated.emit(100)
            self.recommendations_ready.emit(recommendations)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class RecommendationsDialog(QDialog):
    """
    Diálogo avanzado para mostrar recomendaciones de canciones compatibles.
    
    Features:
    - Análisis de compatibilidad DJ profesional
    - Scoring por BPM, tonalidad, energía y mood
    - Información técnica detallada
    - Agregar tracks a playlists
    - Filtros configurables
    """
    
    track_selected = Signal(dict)  # Emitido cuando se selecciona un track para reproducir
    
    def __init__(self, current_track: Dict, parent=None):
        super().__init__(parent)
        self.current_track = current_track
        self.recommendations = []
        self.worker = None
        self.selected_tracks = set()  # Track IDs seleccionados
        self.select_all_checkbox = None
        self.added_tracks = set()  # Track IDs que ya han sido agregados
        
        self.setWindowTitle(f"🎯 Recomendaciones para '{current_track.get('title', 'Unknown')}'")
        self.setModal(False)  # Permitir interacción con ventana principal
        self.resize(1000, 700)
        
        self.setup_ui()
        self.connect_signals()
        self.start_recommendation_generation()
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header con información del track actual
        self.create_header_section(layout)
        
        # Tabs principales
        self.create_tabs_section(layout)
        
        # Botones de acción
        self.create_action_buttons(layout)
        
        # Aplicar estilos
        self.apply_styles()
    
    def create_header_section(self, parent_layout):
        """Crea la sección de header con info del track actual."""
        header_group = QGroupBox("🎵 Track Actual")
        header_layout = QHBoxLayout(header_group)
        
        # Info del track
        track_info = QLabel()
        title = self.current_track.get('title', 'Unknown')
        artist = self.current_track.get('artist', 'Unknown')
        bpm = self.current_track.get('bpm', 'N/A')
        key = self.current_track.get('key', 'Unknown')
        genre = self.current_track.get('genre', 'Unknown')
        
        track_info.setText(f"""
        <b>{title}</b> - {artist}<br>
        🎛️ {bpm} BPM | 🎼 {key} | 🎨 {genre}
        """)
        track_info.setProperty("class", "track_info")
        
        # Controles de filtros
        filters_layout = QVBoxLayout()
        filters_layout.addWidget(QLabel("Filtros:"))
        
        # Controles de filtro
        filter_controls = QHBoxLayout()
        
        filter_controls.addWidget(QLabel("Mín. Score:"))
        self.min_score_spin = QSpinBox()
        self.min_score_spin.setRange(0, 100)
        self.min_score_spin.setValue(40)
        self.min_score_spin.setSuffix("%")
        filter_controls.addWidget(self.min_score_spin)
        
        filter_controls.addWidget(QLabel("Límite:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(5, 50)
        self.limit_spin.setValue(20)
        filter_controls.addWidget(self.limit_spin)
        
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setProperty("class", "btn_primary")
        filter_controls.addWidget(self.refresh_btn)
        
        filters_layout.addLayout(filter_controls)
        
        header_layout.addWidget(track_info, 2)
        header_layout.addLayout(filters_layout, 1)
        
        parent_layout.addWidget(header_group)
    
    def create_tabs_section(self, parent_layout):
        """Crea las tabs principales."""
        self.tabs = QTabWidget()
        
        # Tab 1: Lista de recomendaciones
        self.create_recommendations_tab()
        
        # Tab 2: Análisis detallado
        self.create_analysis_tab()
        
        parent_layout.addWidget(self.tabs)
    
    def create_recommendations_tab(self):
        """Crea la tab de lista de recomendaciones."""
        recommendations_widget = QWidget()
        layout = QVBoxLayout(recommendations_widget)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tabla de recomendaciones
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(9)
        self.recommendations_table.setHorizontalHeaderLabels([
            "☑️", "Title", "Artist", "Score", "BPM", "Key", "Transition", "Quality", "Actions"
        ])
        
        # Configurar tabla
        self.recommendations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recommendations_table.setAlternatingRowColors(True)
        self.recommendations_table.verticalHeader().setVisible(False)
        
        # Auto-resize columnas
        header = self.recommendations_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)    # Checkbox
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Title
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Artist
        header.setSectionResizeMode(3, QHeaderView.Fixed)    # Score
        header.setSectionResizeMode(4, QHeaderView.Fixed)    # BPM
        header.setSectionResizeMode(5, QHeaderView.Fixed)    # Key
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Transition
        header.setSectionResizeMode(7, QHeaderView.Fixed)    # Quality
        header.setSectionResizeMode(8, QHeaderView.Fixed)    # Actions
        
        self.recommendations_table.setColumnWidth(0, 40)  # Checkbox
        self.recommendations_table.setColumnWidth(3, 80)  # Score
        self.recommendations_table.setColumnWidth(4, 80)  # BPM
        self.recommendations_table.setColumnWidth(5, 60)  # Key
        self.recommendations_table.setColumnWidth(7, 80)  # Quality
        self.recommendations_table.setColumnWidth(8, 120) # Actions
        
        layout.addWidget(self.recommendations_table)
        
        # Label de estado
        self.status_label = QLabel("Generando recomendaciones...")
        self.status_label.setProperty("class", "status_label")
        layout.addWidget(self.status_label)
        
        # Panel de acciones masivas
        self.create_batch_actions_panel(layout)
        
        self.tabs.addTab(recommendations_widget, "🎯 Recomendaciones")
    
    def create_analysis_tab(self):
        """Crea la tab de análisis detallado."""
        analysis_widget = QWidget()
        layout = QVBoxLayout(analysis_widget)
        
        # Splitter para dividir la vista
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Resumen estadístico
        stats_group = QGroupBox("📊 Estadísticas")
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(200)
        self.stats_text.setReadOnly(True)
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.addWidget(self.stats_text)
        
        # Panel derecho: Análisis detallado de track seleccionado
        details_group = QGroupBox("🔍 Análisis Detallado")
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        details_layout = QVBoxLayout(details_group)
        details_layout.addWidget(self.analysis_text)
        
        splitter.addWidget(stats_group)
        splitter.addWidget(details_group)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
        self.tabs.addTab(analysis_widget, "📈 Análisis")
    
    def create_batch_actions_panel(self, parent_layout):
        """Crea el panel de acciones masivas."""
        self.batch_panel = QGroupBox("🎛️ Acciones Masivas")
        self.batch_panel.setVisible(False)  # Oculto inicialmente
        batch_layout = QVBoxLayout(self.batch_panel)
        
        # Header con información de selección
        self.selection_info_label = QLabel("0 tracks seleccionados")
        self.selection_info_label.setProperty("class", "selection_info")
        batch_layout.addWidget(self.selection_info_label)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        # Seleccionar todos/ninguno
        self.select_all_btn = QPushButton("☑️ Seleccionar Todos")
        self.select_all_btn.clicked.connect(self.select_all_tracks)
        self.select_all_btn.setProperty("class", "btn_secondary")
        
        self.select_none_btn = QPushButton("⬜ Deseleccionar")
        self.select_none_btn.clicked.connect(self.select_no_tracks)
        self.select_none_btn.setProperty("class", "btn_secondary")
        
        # Selección por calidad
        self.select_excellent_btn = QPushButton("⭐ Seleccionar Excellent (80%+)")
        self.select_excellent_btn.clicked.connect(self.select_excellent_tracks)
        self.select_excellent_btn.setProperty("class", "btn_secondary")
        
        buttons_layout.addWidget(self.select_all_btn)
        buttons_layout.addWidget(self.select_none_btn)
        buttons_layout.addWidget(self.select_excellent_btn)
        buttons_layout.addStretch()
        
        batch_layout.addLayout(buttons_layout)
        
        # Botones de acción principal
        main_actions_layout = QHBoxLayout()
        
        # Crear mix completo
        self.create_mix_btn = QPushButton("🎯 Crear Mix Completo")
        self.create_mix_btn.clicked.connect(self.create_complete_mix)
        self.create_mix_btn.setProperty("class", "btn_primary")
        self.create_mix_btn.setToolTip("Crea una playlist con el track original + todas las recomendaciones")
        
        # Agregar seleccionados
        self.add_selected_btn = QPushButton("➕ Agregar Seleccionados")
        self.add_selected_btn.clicked.connect(self.add_selected_to_playlist)
        self.add_selected_btn.setProperty("class", "btn_primary")
        self.add_selected_btn.setEnabled(False)
        
        # Agregar mejores
        self.add_best_btn = QPushButton("✨ Agregar Mejores (80%+)")
        self.add_best_btn.clicked.connect(self.add_best_to_playlist)
        self.add_best_btn.setProperty("class", "btn_primary")
        
        main_actions_layout.addWidget(self.create_mix_btn)
        main_actions_layout.addWidget(self.add_selected_btn)
        main_actions_layout.addWidget(self.add_best_btn)
        main_actions_layout.addStretch()
        
        batch_layout.addLayout(main_actions_layout)
        
        parent_layout.addWidget(self.batch_panel)
    
    def create_action_buttons(self, parent_layout):
        """Crea los botones de acción."""
        buttons_layout = QHBoxLayout()
        
        # Botón de cerrar
        self.close_btn = QPushButton("❌ Cerrar")
        self.close_btn.clicked.connect(self.close)
        
        # Botón de ayuda
        self.help_btn = QPushButton("❓ Ayuda")
        self.help_btn.clicked.connect(self.show_help)
        
        buttons_layout.addWidget(self.help_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn)
        
        parent_layout.addLayout(buttons_layout)
    
    def connect_signals(self):
        """Conecta las señales."""
        self.refresh_btn.clicked.connect(self.start_recommendation_generation)
        self.recommendations_table.itemSelectionChanged.connect(self.on_recommendation_selected)
        self.recommendations_table.itemDoubleClicked.connect(self.on_recommendation_double_clicked)
    
    def start_recommendation_generation(self):
        """Inicia la generación de recomendaciones en background."""
        try:
            print(f"🎯 Iniciando generación de recomendaciones para: {self.current_track.get('title', 'Unknown')}")
            
            # Limpiar worker anterior si existe
            if self.worker and self.worker.isRunning():
                print("🔄 Terminando worker anterior...")
                self.worker.quit()
                self.worker.wait(3000)  # Esperar máximo 3 segundos
                if self.worker.isRunning():
                    print("⚠️ Worker anterior no terminó correctamente")
                    self.worker.terminate()
            
            # Validar track actual
            if not self.current_track or not self.current_track.get('id'):
                self.on_error("Track actual no válido o sin ID")
                return
            
            # Configurar UI para estado de carga
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("🔄 Generando recomendaciones...")
            self.recommendations_table.setRowCount(0)
            self.refresh_btn.setEnabled(False)
            
            # Obtener filtros
            min_score = self.min_score_spin.value() / 100.0
            limit = self.limit_spin.value()
            
            print(f"📊 Configuración: min_score={min_score:.2f}, limit={limit}")
            
            # Crear y iniciar worker
            self.worker = RecommendationWorker(self.current_track, limit, min_score)
            self.worker.recommendations_ready.connect(self.on_recommendations_ready)
            self.worker.error_occurred.connect(self.on_error)
            self.worker.progress_updated.connect(self.progress_bar.setValue)
            self.worker.finished.connect(self._on_worker_finished)
            
            print("🚀 Iniciando worker thread...")
            self.worker.start()
            
        except Exception as e:
            print(f"❌ Error iniciando generación de recomendaciones: {e}")
            self.on_error(f"Error iniciando análisis: {str(e)}")
    
    def _on_worker_finished(self):
        """Maneja cuando el worker termina."""
        print("✅ Worker thread terminado")
        self.refresh_btn.setEnabled(True)
    
    def on_recommendations_ready(self, recommendations):
        """Maneja cuando las recomendaciones están listas."""
        self.recommendations = recommendations
        self.progress_bar.setVisible(False)
        
        if not recommendations:
            self.status_label.setText("❌ No se encontraron recomendaciones compatibles")
            return
        
        self.populate_recommendations_table()
        self.update_analysis_stats()
        self.status_label.setText(f"✅ {len(recommendations)} recomendaciones encontradas")
        
        # Actualizar panel de acciones masivas
        self.update_batch_actions_panel()
    
    def on_error(self, error_msg):
        """Maneja errores en la generación."""
        print(f"❌ Error en diálogo de recomendaciones: {error_msg}")
        
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"❌ Error: {error_msg}")
        
        # Mostrar mensaje de error más amigable
        user_msg = "No se pudieron generar recomendaciones."
        if "no válido" in error_msg.lower():
            user_msg += "\n\nVerifica que la canción tenga datos de BPM y tonalidad."
        elif "conexión" in error_msg.lower() or "database" in error_msg.lower():
            user_msg += "\n\nProblema de conexión con la base de datos."
        else:
            user_msg += f"\n\nDetalle técnico: {error_msg}"
        
        QMessageBox.warning(self, "Error en Recomendaciones", user_msg)
    
    def populate_recommendations_table(self):
        """Puebla la tabla con las recomendaciones."""
        self.recommendations_table.setRowCount(len(self.recommendations))
        
        for row, (track, analysis) in enumerate(self.recommendations):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(track.get('id') in self.selected_tracks)
            checkbox.stateChanged.connect(lambda state, t_id=track.get('id'): self.on_track_selection_changed(t_id, state == Qt.Checked))
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.recommendations_table.setCellWidget(row, 0, checkbox_widget)
            
            # Title
            title_text = track.get('title', 'Unknown')
            if track.get('id') in self.added_tracks:
                title_text += " ✅"
            title_item = QTableWidgetItem(title_text)
            title_item.setData(Qt.UserRole, track)  # Guardar datos del track
            
            # Marcar visualmente tracks ya agregados
            if track.get('id') in self.added_tracks:
                title_item.setBackground(Qt.Color(200, 255, 200))  # Verde claro
                title_item.setToolTip("Este track ya ha sido agregado a una playlist")
            
            self.recommendations_table.setItem(row, 1, title_item)
            
            # Artist
            self.recommendations_table.setItem(row, 2, QTableWidgetItem(track.get('artist', 'Unknown')))
            
            # Score con color
            score_item = QTableWidgetItem(f"{analysis.overall_score:.1%}")
            score_item.setData(Qt.UserRole, analysis)  # Guardar análisis
            
            # Colorear según score
            if analysis.overall_score >= 0.8:
                score_item.setBackground(Qt.green)
            elif analysis.overall_score >= 0.6:
                score_item.setBackground(Qt.yellow)
            else:
                score_item.setBackground(Qt.red)
            
            self.recommendations_table.setItem(row, 3, score_item)
            
            # BPM
            bpm = track.get('bpm', 0)
            bpm_text = f"{bpm:.0f}" if bpm and bpm > 0 else "N/A"
            self.recommendations_table.setItem(row, 4, QTableWidgetItem(bpm_text))
            
            # Key
            self.recommendations_table.setItem(row, 5, QTableWidgetItem(track.get('key', 'Unknown')))
            
            # Transition Type
            transition_type = analysis.recommended_type.value.replace('_', ' ').title()
            self.recommendations_table.setItem(row, 6, QTableWidgetItem(transition_type))
            
            # Quality
            quality = analysis.transition_quality.value.title()
            self.recommendations_table.setItem(row, 7, QTableWidgetItem(quality))
            
            # Actions - botones
            actions_widget = self.create_action_buttons_for_row(track, analysis)
            self.recommendations_table.setCellWidget(row, 8, actions_widget)
    
    def create_action_buttons_for_row(self, track, analysis):
        """Crea botones de acción para una fila."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Botón play
        play_btn = QPushButton("▶️")
        play_btn.setToolTip("Reproducir")
        play_btn.setMaximumWidth(30)
        play_btn.clicked.connect(lambda: self.play_track(track))
        
        # Botón add to playlist
        add_btn = QPushButton("➕")
        add_btn.setToolTip("Agregar a playlist")
        add_btn.setMaximumWidth(30)
        add_btn.clicked.connect(lambda: self.add_to_playlist(track))
        
        layout.addWidget(play_btn)
        layout.addWidget(add_btn)
        
        return widget
    
    def update_analysis_stats(self):
        """Actualiza las estadísticas de análisis."""
        if not self.recommendations:
            return
        
        # Calcular estadísticas
        scores = [analysis.overall_score for _, analysis in self.recommendations]
        avg_score = sum(scores) / len(scores)
        
        # Contar por calidad
        quality_counts = {}
        transition_counts = {}
        
        for _, analysis in self.recommendations:
            quality = analysis.transition_quality.value
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            
            transition = analysis.recommended_type.value
            transition_counts[transition] = transition_counts.get(transition, 0) + 1
        
        # Crear texto de estadísticas
        stats_text = f"""
<h3>📊 Resumen Estadístico</h3>
<b>Total recomendaciones:</b> {len(self.recommendations)}<br>
<b>Score promedio:</b> {avg_score:.1%}<br><br>

<b>Por Calidad:</b><br>
"""
        
        for quality, count in quality_counts.items():
            percentage = (count / len(self.recommendations)) * 100
            stats_text += f"• {quality.title()}: {count} ({percentage:.0f}%)<br>"
        
        stats_text += "<br><b>Por Tipo de Transición:</b><br>"
        for transition, count in transition_counts.items():
            percentage = (count / len(self.recommendations)) * 100
            transition_name = transition.replace('_', ' ').title()
            stats_text += f"• {transition_name}: {count} ({percentage:.0f}%)<br>"
        
        self.stats_text.setHtml(stats_text)
    
    def on_track_selection_changed(self, track_id, is_selected):
        """Maneja cambios en la selección de tracks individuales."""
        if is_selected:
            self.selected_tracks.add(track_id)
        else:
            self.selected_tracks.discard(track_id)
        
        # Actualizar el panel de acciones masivas
        self.update_batch_actions_panel()
    
    def update_batch_actions_panel(self):
        """Actualiza la visibilidad y estado del panel de acciones masivas."""
        if not hasattr(self, 'batch_panel'):
            return
            
        selected_count = len(self.selected_tracks)
        total_count = len(self.recommendations)
        
        # Mostrar panel solo si hay recomendaciones
        self.batch_panel.setVisible(total_count > 0)
        
        # Actualizar texto de información
        if selected_count > 0:
            self.selection_info_label.setText(f"✅ {selected_count} de {total_count} tracks seleccionados")
            self.selection_info_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        else:
            self.selection_info_label.setText(f"{total_count} tracks disponibles - Ninguno seleccionado")
            self.selection_info_label.setStyleSheet("color: #666; font-style: italic;")
        
        # Habilitar/deshabilitar botones según selección
        self.add_selected_btn.setEnabled(selected_count > 0)
        self.add_selected_btn.setText(f"➕ Agregar Seleccionados ({selected_count})")
        
        # Contar tracks con score >= 80%
        excellent_count = sum(1 for _, analysis in self.recommendations if analysis.overall_score >= 0.8)
        self.add_best_btn.setText(f"✨ Agregar Mejores ({excellent_count})")
        self.add_best_btn.setEnabled(excellent_count > 0)
        self.select_excellent_btn.setText(f"⭐ Seleccionar Excellent ({excellent_count})")
        self.select_excellent_btn.setEnabled(excellent_count > 0)
    
    def on_recommendation_selected(self):
        """Maneja la selección de una recomendación."""
        current_row = self.recommendations_table.currentRow()
        if current_row < 0 or current_row >= len(self.recommendations):
            return
        
        track, analysis = self.recommendations[current_row]
        self.show_detailed_analysis(track, analysis)
    
    def on_recommendation_double_clicked(self, item):
        """Maneja doble click en una recomendación."""
        row = item.row()
        if row < 0 or row >= len(self.recommendations):
            return
        
        track, analysis = self.recommendations[row]
        self.play_track(track)
    
    def show_detailed_analysis(self, track, analysis):
        """Muestra análisis detallado de un track."""
        title = track.get('title', 'Unknown')
        artist = track.get('artist', 'Unknown')
        
        # Crear HTML detallado
        html = f"""
<h3>🔍 Análisis Detallado</h3>
<b>Track:</b> {title} - {artist}<br><br>

<h4>🎯 Puntuación General: {analysis.overall_score:.1%}</h4>
<b>Calidad:</b> {analysis.transition_quality.value.title()}<br>
<b>Tipo recomendado:</b> {analysis.recommended_type.value.replace('_', ' ').title()}<br><br>

<h4>📊 Compatibilidades Específicas:</h4>
• <b>BPM:</b> {analysis.bpm_compatibility:.1%}<br>
• <b>Tonalidad tradicional:</b> {analysis.key_compatibility:.1%}<br>
• <b>Fuzzy Keymixing:</b> {analysis.fuzzy_key_compatibility:.1%}<br>
• <b>Energía:</b> {analysis.energy_compatibility:.1%}<br>
• <b>Mood:</b> {analysis.mood_compatibility:.1%}<br><br>

<h4>⚙️ Detalles Técnicos:</h4>
• <b>Ratio BPM:</b> {analysis.bpm_ratio:.2f}<br>
• <b>Relación tonal:</b> {analysis.key_relationship}<br>
• <b>Relación fuzzy:</b> {analysis.fuzzy_key_relationship}<br>
• <b>Delta energía:</b> {analysis.energy_delta:+.2f}<br>
• <b>Punto de salida:</b> {analysis.mix_out_point:.1f}s<br>
• <b>Punto de entrada:</b> {analysis.mix_in_point:.1f}s<br>
• <b>Duración crossfade:</b> {analysis.crossfade_duration:.1f}s<br><br>

<h4>💡 Recomendaciones:</h4>
"""
        
        for rec in analysis.recommendations:
            html += f"• {rec}<br>"
        
        if analysis.warnings:
            html += "<br><h4>⚠️ Advertencias:</h4>"
            for warning in analysis.warnings:
                html += f"• {warning}<br>"
        
        if analysis.pitch_shift_recommendation:
            ps = analysis.pitch_shift_recommendation
            html += f"""<br><h4>🎛️ Pitch Shift Recomendado:</h4>
• <b>Ajuste:</b> {ps['shift_semitones']:+.1f} semitonos ({ps['direction']})<br>
• <b>Mejora:</b> {ps['improvement']:.1%}<br>
• <b>Confianza:</b> {ps['confidence']:.1%}<br>
• <b>Explicación:</b> {ps['explanation']}<br>"""
        
        self.analysis_text.setHtml(html)
    
    def play_track(self, track):
        """Reproduce un track recomendado."""
        print(f"🎵 Playing recommended track: {track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')}")
        self.track_selected.emit(track)
    
    def add_to_playlist(self, track):
        """Agrega un track a una playlist."""
        try:
            print(f"➕ Agregando track a playlist: {track.get('title', 'Unknown')}")
            
            from ui.components.playlist_dialog import PlaylistDialog
            from services.playlist_service import PlaylistService
            from core.database import get_db_path
            
            # Validar track
            if not track or not track.get('id'):
                QMessageBox.warning(self, "Error", "Track no válido para agregar a playlist.")
                return
            
            playlist_service = PlaylistService(get_db_path())
            
            # Obtener playlists existentes
            existing_playlists = playlist_service.get_all_playlists()
            print(f"📂 {len(existing_playlists)} playlists encontradas")
            
            # Crear menú para seleccionar playlist
            from PySide6.QtWidgets import QMenu
            from PySide6.QtGui import QAction
            menu = QMenu("Agregar a Playlist", self)
            
            # Opción para crear nueva playlist
            create_new_action = QAction("➕ Nueva Playlist", self)
            create_new_action.triggered.connect(lambda: self.create_new_playlist_with_track(track))
            menu.addAction(create_new_action)
            
            if existing_playlists:
                menu.addSeparator()
                menu.addSection("📂 Playlists Existentes")
                
                for playlist in existing_playlists:
                    playlist_name = playlist['name']
                    track_count = playlist.get('track_count', 0)
                    action_text = f"📝 {playlist_name} ({track_count} tracks)"
                    
                    action = QAction(action_text, self)
                    action.triggered.connect(lambda checked, pid=playlist['id'], name=playlist_name: 
                                           self.add_track_to_existing_playlist(track, pid, name))
                    menu.addAction(action)
            else:
                menu.addSeparator()
                no_playlists_action = QAction("(No hay playlists disponibles)", self)
                no_playlists_action.setEnabled(False)
                menu.addAction(no_playlists_action)
            
            # Mostrar menú en posición del cursor
            global_pos = self.mapToGlobal(self.rect().center())
            menu.exec(global_pos)
            
        except ImportError as e:
            print(f"❌ Error importando módulos: {e}")
            QMessageBox.critical(self, "Error", "No se pudieron cargar los componentes necesarios.")
        except Exception as e:
            print(f"❌ Error showing playlist menu: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo mostrar el menú de playlists:\n\n{str(e)}")
    
    def create_new_playlist_with_track(self, track):
        """Crea una nueva playlist con el track recomendado."""
        try:
            print(f"📝 Creando nueva playlist con track: {track.get('title', 'Unknown')}")
            
            from ui.components.playlist_dialog import PlaylistDialog
            from services.playlist_service import PlaylistService
            from core.database import get_db_path
            
            # Validar track antes de proceder
            if not track or not track.get('id'):
                QMessageBox.warning(self, "Error", "Track no válido para crear playlist.")
                return
            
            dialog = PlaylistDialog(self)
            
            if dialog.exec() == QDialog.Accepted:
                playlist_service = PlaylistService(get_db_path())
                playlist_data = dialog.get_playlist_data()
                
                print(f"📂 Creando playlist: {playlist_data['name']}")
                
                # Crear la playlist
                playlist_id = playlist_service.create_playlist(
                    playlist_data['name'],
                    playlist_data['description'],
                    playlist_data['color']
                )
                
                if playlist_id:
                    # Agregar el track
                    track_id = track.get('id')
                    print(f"➕ Agregando track ID {track_id} a playlist ID {playlist_id}")
                    
                    success = playlist_service.add_tracks_to_playlist(playlist_id, [track_id])
                    
                    if success:
                        print(f"✅ Playlist creada exitosamente")
                        QMessageBox.information(
                            self, 
                            "Playlist Creada", 
                            f"Playlist '{playlist_data['name']}' creada exitosamente con:\n'{track.get('title', 'Unknown')}'"
                        )
                    else:
                        print(f"❌ Error agregando track a playlist")
                        QMessageBox.warning(self, "Error", 
                                          f"Playlist creada pero no se pudo agregar el track.\n"
                                          f"Puedes agregarlo manualmente desde la biblioteca.")
                else:
                    print(f"❌ Error creando playlist")
                    QMessageBox.warning(self, "Error", "No se pudo crear la playlist.")
            else:
                print("👋 Usuario canceló creación de playlist")
                
        except Exception as e:
            print(f"❌ Error creando playlist: {e}")
            QMessageBox.critical(self, "Error", f"Error creando playlist:\n\n{str(e)}")
    
    def add_track_to_existing_playlist(self, track, playlist_id, playlist_name):
        """Agrega el track a una playlist existente."""
        try:
            print(f"➕ Agregando '{track.get('title', 'Unknown')}' a playlist '{playlist_name}'")
            
            from services.playlist_service import PlaylistService
            from core.database import get_db_path
            
            # Validar parámetros
            track_id = track.get('id')
            if not track_id:
                QMessageBox.warning(self, "Error", "Track sin ID válido.")
                return
            
            if not playlist_id:
                QMessageBox.warning(self, "Error", "Playlist ID no válido.")
                return
            
            playlist_service = PlaylistService(get_db_path())
            success = playlist_service.add_tracks_to_playlist(playlist_id, [track_id])
            
            if success:
                print(f"✅ Track agregado exitosamente a '{playlist_name}'")
                QMessageBox.information(
                    self, 
                    "Track Agregado", 
                    f"'{track.get('title', 'Unknown')}' agregado exitosamente a:\n'{playlist_name}'"
                )
            else:
                print(f"❌ Error agregando track a '{playlist_name}'")
                QMessageBox.warning(self, "Error", 
                                  f"No se pudo agregar el track a '{playlist_name}'.\n\n"
                                  f"Posibles causas:\n"
                                  f"• El track ya está en la playlist\n"
                                  f"• Error de base de datos\n"
                                  f"• Permisos insuficientes")
                
        except Exception as e:
            print(f"❌ Error agregando track a playlist: {e}")
            QMessageBox.critical(self, "Error", f"Error agregando track a playlist:\n\n{str(e)}")
    
    def show_help(self):
        """Muestra información de ayuda."""
        help_text = """
<h3>🎯 Sistema de Recomendaciones DJ</h3>

<h4>¿Cómo funciona?</h4>
El sistema analiza tu canción actual y encuentra tracks compatibles basándose en:

<b>🎛️ BPM (35%):</b> Compatibilidad de tempo, incluyendo ratios musicales (2:1, 3:2, etc.)<br>
<b>🎼 Tonalidad (25%):</b> Análisis armónico tradicional + Fuzzy Keymixing avanzado<br>
<b>⚡ Energía (25%):</b> Flujo de energía para mantener el dancefloor<br>
<b>🎨 Mood (15%):</b> Compatibilidad de valence, danceability y acousticness<br>

<h4>🏆 Calidades de Transición:</h4>
• <b>Excellent (90-100%):</b> Transición perfecta<br>
• <b>Good (70-89%):</b> Muy buena compatibilidad<br>
• <b>Fair (50-69%):</b> Compatibilidad moderada<br>
• <b>Poor (30-49%):</b> Requiere trabajo del DJ<br>
• <b>Bad (0-29%):</b> No recomendado<br>

<h4>🔄 Tipos de Transición:</h4>
• <b>Harmonic Mix:</b> Mezcla armónica tradicional<br>
• <b>Fuzzy Harmonic Mix:</b> Mezcla con flexibilidad tonal<br>
• <b>Beatmatch:</b> Enfoque en compatibilidad de BPM<br>
• <b>Pitch Shift Mix:</b> Requiere ajuste de pitch<br>
• <b>Energy Transition:</b> Cambio de energía controlado<br>

<h4>💡 Consejos:</h4>
• Usa el <b>Mín. Score</b> para filtrar por calidad<br>
• Revisa el <b>Análisis Detallado</b> para entender cada recomendación<br>
• Experimenta con diferentes tipos de transición<br>
"""
        
        QMessageBox.information(self, "Ayuda - Recomendaciones DJ", help_text)
    
    # === MÉTODOS DE SELECCIÓN MASIVA ===
    
    def select_all_tracks(self):
        """Selecciona todos los tracks."""
        self.selected_tracks.clear()
        for track, _ in self.recommendations:
            self.selected_tracks.add(track.get('id'))
        
        # Actualizar checkboxes en la tabla
        self.refresh_table_checkboxes()
        self.update_batch_actions_panel()
    
    def select_no_tracks(self):
        """Deselecciona todos los tracks."""
        self.selected_tracks.clear()
        
        # Actualizar checkboxes en la tabla
        self.refresh_table_checkboxes()
        self.update_batch_actions_panel()
    
    def select_excellent_tracks(self):
        """Selecciona solo tracks con score >= 80%."""
        self.selected_tracks.clear()
        for track, analysis in self.recommendations:
            if analysis.overall_score >= 0.8:
                self.selected_tracks.add(track.get('id'))
        
        # Actualizar checkboxes en la tabla
        self.refresh_table_checkboxes()
        self.update_batch_actions_panel()
    
    def refresh_table_checkboxes(self):
        """Actualiza el estado de todos los checkboxes en la tabla."""
        for row in range(self.recommendations_table.rowCount()):
            checkbox_widget = self.recommendations_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    track = self.recommendations[row][0]
                    checkbox.setChecked(track.get('id') in self.selected_tracks)
    
    # === MÉTODOS DE ACCIONES MASIVAS ===
    
    def create_complete_mix(self):
        """Crea una playlist completa con track original + todas las recomendaciones."""
        try:
            print("🎯 Creando mix completo...")
            
            from ui.components.playlist_dialog import PlaylistDialog
            from services.playlist_service import PlaylistService
            from core.database import get_db_path
            
            # Crear nombre sugerido para la playlist
            current_title = self.current_track.get('title', 'Unknown')
            current_artist = self.current_track.get('artist', 'Unknown')
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            suggested_name = f"Mix Compatible - {current_title} - {date_str}"
            
            # Mostrar diálogo de creación de playlist con nombre pre-llenado
            dialog = PlaylistDialog(self)
            dialog.name_edit.setText(suggested_name)
            dialog.description_edit.setPlainText(
                f"Mix automático basado en '{current_title}' por {current_artist}\\n"
                f"Incluye {len(self.recommendations)} recomendaciones compatibles."
            )
            
            if dialog.exec() == QDialog.Accepted:
                playlist_service = PlaylistService(get_db_path())
                playlist_data = dialog.get_playlist_data()
                
                print(f"📂 Creando playlist: {playlist_data['name']}")
                
                # Crear la playlist
                playlist_id = playlist_service.create_playlist(
                    playlist_data['name'],
                    playlist_data['description'],
                    playlist_data['color']
                )
                
                if playlist_id:
                    # Preparar lista de tracks: original + recomendaciones
                    track_ids = [self.current_track.get('id')]
                    track_ids.extend([track.get('id') for track, _ in self.recommendations])
                    
                    print(f"➕ Agregando {len(track_ids)} tracks a playlist")
                    success = playlist_service.add_tracks_to_playlist(playlist_id, track_ids)
                    
                    if success:
                        print("✅ Mix completo creado exitosamente")
                        QMessageBox.information(
                            self, 
                            "Mix Creado", 
                            f"¡Mix completo creado exitosamente!\\n\\n"
                            f"Playlist: '{playlist_data['name']}'\\n"
                            f"Tracks: {len(track_ids)} (original + {len(self.recommendations)} recomendaciones)\\n\\n"
                            f"🎵 Tu mix está listo para la sesión DJ"
                        )
                        # No cerrar el diálogo para permitir más acciones
                    else:
                        print("❌ Error agregando tracks al mix")
                        QMessageBox.warning(self, "Error", "Playlist creada pero algunos tracks no se pudieron agregar.")
                else:
                    print("❌ Error creando playlist")
                    QMessageBox.warning(self, "Error", "No se pudo crear la playlist.")
            
        except Exception as e:
            print(f"❌ Error creando mix completo: {e}")
            QMessageBox.critical(self, "Error", f"Error creando mix completo:\\n\\n{str(e)}")
    
    def add_selected_to_playlist(self):
        """Agrega los tracks seleccionados a una playlist."""
        if not self.selected_tracks:
            QMessageBox.information(self, "Sin Selección", "No hay tracks seleccionados para agregar.")
            return
        
        try:
            print(f"➕ Agregando {len(self.selected_tracks)} tracks seleccionados...")
            
            from ui.components.playlist_dialog import PlaylistDialog
            from services.playlist_service import PlaylistService
            from core.database import get_db_path
            from PySide6.QtWidgets import QMenu
            from PySide6.QtGui import QAction
            
            playlist_service = PlaylistService(get_db_path())
            existing_playlists = playlist_service.get_all_playlists()
            
            # Crear menú para seleccionar playlist
            menu = QMenu("Agregar Seleccionados a Playlist", self)
            
            # Opción para crear nueva playlist
            create_new_action = QAction("➕ Nueva Playlist", self)
            create_new_action.triggered.connect(lambda: self.create_new_playlist_with_selected())
            menu.addAction(create_new_action)
            
            if existing_playlists:
                menu.addSeparator()
                menu.addSection("📂 Playlists Existentes")
                
                for playlist in existing_playlists:
                    playlist_name = playlist['name']
                    track_count = playlist.get('track_count', 0)
                    action_text = f"📝 {playlist_name} ({track_count} tracks)"
                    
                    action = QAction(action_text, self)
                    action.triggered.connect(lambda checked, pid=playlist['id'], name=playlist_name: 
                                           self.add_selected_to_existing_playlist(pid, name))
                    menu.addAction(action)
            
            # Mostrar menú
            global_pos = self.mapToGlobal(self.rect().center())
            menu.exec(global_pos)
            
        except Exception as e:
            print(f"❌ Error agregando seleccionados: {e}")
            QMessageBox.warning(self, "Error", f"Error agregando tracks seleccionados:\\n\\n{str(e)}")
    
    def add_best_to_playlist(self):
        """Agrega los mejores tracks (score >= 80%) a una playlist."""
        try:
            # Seleccionar automáticamente los mejores tracks
            best_tracks = [track.get('id') for track, analysis in self.recommendations if analysis.overall_score >= 0.8]
            
            if not best_tracks:
                QMessageBox.information(self, "Sin Tracks Excellent", "No hay tracks con puntuación Excellent (80%+) para agregar.")
                return
            
            print(f"✨ Agregando {len(best_tracks)} mejores tracks...")
            
            # Usar la misma lógica que add_selected pero con los mejores tracks
            old_selection = self.selected_tracks.copy()
            self.selected_tracks = set(best_tracks)
            self.add_selected_to_playlist()
            # Restaurar selección original
            self.selected_tracks = old_selection
            self.refresh_table_checkboxes()
            
        except Exception as e:
            print(f"❌ Error agregando mejores tracks: {e}")
            QMessageBox.warning(self, "Error", f"Error agregando mejores tracks:\\n\\n{str(e)}")
    
    def create_new_playlist_with_selected(self):
        """Crea una nueva playlist con los tracks seleccionados."""
        try:
            selected_tracks_data = [track for track, _ in self.recommendations if track.get('id') in self.selected_tracks]
            
            if not selected_tracks_data:
                QMessageBox.warning(self, "Error", "No hay tracks seleccionados.")
                return
            
            from ui.components.playlist_dialog import PlaylistDialog
            from services.playlist_service import PlaylistService
            from core.database import get_db_path
            from datetime import datetime
            
            # Crear nombre sugerido
            current_title = self.current_track.get('title', 'Unknown')
            date_str = datetime.now().strftime("%Y-%m-%d")
            suggested_name = f"Selección - {current_title} - {date_str}"
            
            dialog = PlaylistDialog(self)
            dialog.name_edit.setText(suggested_name)
            dialog.description_edit.setPlainText(
                f"Selección personalizada de {len(selected_tracks_data)} tracks compatibles con '{current_title}'."
            )
            
            if dialog.exec() == QDialog.Accepted:
                playlist_service = PlaylistService(get_db_path())
                playlist_data = dialog.get_playlist_data()
                
                playlist_id = playlist_service.create_playlist(
                    playlist_data['name'],
                    playlist_data['description'],
                    playlist_data['color']
                )
                
                if playlist_id:
                    success = playlist_service.add_tracks_to_playlist(playlist_id, list(self.selected_tracks))
                    
                    if success:
                        QMessageBox.information(
                            self, 
                            "Playlist Creada", 
                            f"Playlist '{playlist_data['name']}' creada con {len(self.selected_tracks)} tracks seleccionados."
                        )
                    else:
                        QMessageBox.warning(self, "Error", "Playlist creada pero algunos tracks no se pudieron agregar.")
                else:
                    QMessageBox.warning(self, "Error", "No se pudo crear la playlist.")
        
        except Exception as e:
            print(f"❌ Error creando playlist con seleccionados: {e}")
            QMessageBox.critical(self, "Error", f"Error creando playlist:\\n\\n{str(e)}")
    
    def add_selected_to_existing_playlist(self, playlist_id, playlist_name):
        """Agrega los tracks seleccionados a una playlist existente."""
        try:
            print(f"➕ Agregando {len(self.selected_tracks)} tracks a '{playlist_name}'")
            
            from services.playlist_service import PlaylistService
            from core.database import get_db_path
            
            playlist_service = PlaylistService(get_db_path())
            success = playlist_service.add_tracks_to_playlist(playlist_id, list(self.selected_tracks))
            
            if success:
                print(f"✅ Tracks agregados exitosamente a '{playlist_name}'")
                QMessageBox.information(
                    self, 
                    "Tracks Agregados", 
                    f"{len(self.selected_tracks)} tracks agregados exitosamente a:\\n'{playlist_name}'"
                )
            else:
                print(f"❌ Error agregando tracks a '{playlist_name}'")
                QMessageBox.warning(self, "Error", f"No se pudieron agregar todos los tracks a '{playlist_name}'.")
                
        except Exception as e:
            print(f"❌ Error agregando a playlist existente: {e}")
            QMessageBox.critical(self, "Error", f"Error agregando tracks:\\n\\n{str(e)}")
    
    def apply_styles(self):
        """Aplica estilos personalizados."""
        self.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 8px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QLabel[class="track_info"] {
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            font-size: 12px;
        }
        
        QLabel[class="status_label"] {
            color: #666;
            font-style: italic;
            padding: 4px;
        }
        
        QPushButton[class="btn_primary"] {
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }
        
        QPushButton[class="btn_primary"]:hover {
            background: #1976D2;
        }
        
        QPushButton[class="btn_secondary"] {
            background: #757575;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }
        
        QPushButton[class="btn_secondary"]:hover {
            background: #616161;
        }
        
        QLabel[class="selection_info"] {
            font-size: 12px;
            padding: 4px 8px;
            background: #f5f5f5;
            border-radius: 3px;
            border-left: 3px solid #2196F3;
        }
        
        QTableWidget {
            gridline-color: #e0e0e0;
            alternate-background-color: #f9f9f9;
        }
        
        QTableWidget::item:selected {
            background: #e3f2fd;
            color: #1976d2;
        }
        """)
    
    def closeEvent(self, event):
        """Maneja el cierre del diálogo."""
        try:
            print("🔄 Cerrando diálogo de recomendaciones...")
            
            # Limpiar worker thread
            if self.worker and self.worker.isRunning():
                print("🛑 Terminando worker thread...")
                self.worker.quit()
                
                # Esperar que termine gracefully
                if not self.worker.wait(3000):  # 3 segundos máximo
                    print("⚠️ Worker no terminó gracefully, forzando...")
                    self.worker.terminate()
                    self.worker.wait(1000)  # 1 segundo más
                
                print("✅ Worker thread terminado")
            
            # Limpiar referencias
            self.worker = None
            self.recommendations = []
            
            print("✅ Diálogo cerrado correctamente")
            event.accept()
            
        except Exception as e:
            print(f"❌ Error cerrando diálogo: {e}")
            # Aceptar el evento de cierre incluso si hay errores
            event.accept()