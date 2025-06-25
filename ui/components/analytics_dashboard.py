"""
Analytics Dashboard for DjAlfin - FIXED VERSION
Professional analytics visualization with PyArrow integration and robust error handling
"""

import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
    QLabel, QScrollArea, QFrame, QSplitter, QGroupBox, QComboBox,
    QLineEdit, QSlider, QCheckBox, QSpinBox, QProgressBar, QTextEdit,
    QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QPalette, QPixmap, QPainter

# Configure Qt API and matplotlib backend with robust fallback
import os
import sys
import warnings

# Set QT_API environment variable for PySide6 compatibility
os.environ['QT_API'] = 'pyside6'

# Configure matplotlib with multiple backend fallback options
import matplotlib
matplotlib_backend_configured = False
matplotlib_canvas_class = None

def configure_matplotlib_backend():
    """Configure matplotlib backend with robust fallback system."""
    global matplotlib_backend_configured, matplotlib_canvas_class
    
    if matplotlib_backend_configured:
        return matplotlib_canvas_class
    
    # Try backends in order of preference
    backends_to_try = [
        ('Qt5Agg', 'matplotlib.backends.backend_qt5agg', 'FigureCanvasQTAgg'),
        ('TkAgg', 'matplotlib.backends.backend_tkagg', 'FigureCanvasTkAgg'), 
        ('Agg', None, None)  # Non-interactive fallback
    ]
    
    for backend_name, module_name, canvas_class_name in backends_to_try:
        try:
            print(f"🔄 Trying matplotlib backend: {backend_name}")
            matplotlib.use(backend_name, force=True)
            
            if module_name and canvas_class_name:
                # Try to import the canvas class
                module = __import__(module_name, fromlist=[canvas_class_name])
                canvas_class = getattr(module, canvas_class_name)
                matplotlib_canvas_class = canvas_class
                print(f"✅ Successfully configured matplotlib backend: {backend_name}")
                matplotlib_backend_configured = True
                return canvas_class
            elif backend_name == 'Agg':
                # Agg backend doesn't need Qt canvas
                print(f"✅ Using Agg backend for non-interactive charts")
                matplotlib_backend_configured = True
                return None
                
        except Exception as e:
            print(f"❌ Backend {backend_name} failed: {e}")
            continue
    
    # If all backends fail, raise an error
    raise ImportError("Could not configure any matplotlib backend")

# Configure matplotlib backend
try:
    FigureCanvas = configure_matplotlib_backend()
except Exception as e:
    print(f"⚠️ Matplotlib backend configuration failed: {e}")
    FigureCanvas = None

# Import matplotlib components with error handling
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.figure import Figure
    import seaborn as sns
    matplotlib_available = True
    print("✅ Matplotlib components imported successfully")
except Exception as e:
    print(f"⚠️ Matplotlib import failed: {e}")
    matplotlib_available = False
    plt = None
    patches = None
    Figure = None
    seaborn = None

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import time
from datetime import datetime

# Import our PyArrow analytics engine
from core.pyarrow_analytics import (
    analytics_engine, get_library_overview, analyze_bpm_patterns,
    find_similar_tracks, generate_smart_playlist, real_time_search
)

# Set style for professional appearance
if matplotlib_available and plt:
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
    except:
        plt.style.use('dark_background')
if matplotlib_available and sns:
    sns.set_palette("husl")


class AnalyticsWorker(QThread):
    """Background worker for analytics computations to keep UI responsive."""
    
    analytics_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, operation: str, params: Dict = None):
        super().__init__()
        self.operation = operation
        self.params = params or {}
        
    def run(self):
        """Execute analytics operation in background thread."""
        try:
            if self.operation == 'overview':
                result = get_library_overview()
                self.analytics_ready.emit({'operation': 'overview', 'data': result})
                
            elif self.operation == 'bpm_analysis':
                result = analyze_bpm_patterns()
                self.analytics_ready.emit({'operation': 'bpm_analysis', 'data': result})
                
            elif self.operation == 'smart_playlist':
                result = generate_smart_playlist(self.params.get('criteria', {}), 
                                               self.params.get('limit', 50))
                self.analytics_ready.emit({'operation': 'smart_playlist', 'data': result})
                
            elif self.operation == 'real_time_search':
                result = real_time_search(self.params.get('filters', {}))
                self.analytics_ready.emit({'operation': 'real_time_search', 'data': result})
                
        except Exception as e:
            self.error_occurred.emit(f"Analytics error: {str(e)}")


class AnalyticsDashboard(QWidget):
    """
    Main Analytics Dashboard for DjAlfin with PyArrow integration.
    Provides comprehensive library analytics and real-time insights.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set backend info as instance variable
        self.backend_info = "PyArrow + Polars"
        if matplotlib_available and FigureCanvas:
            self.backend_info += " + Interactive Charts"
        elif matplotlib_available:
            self.backend_info += " + Static Charts (Agg backend)"
        else:
            self.backend_info += " + Text Analytics (Charts unavailable)"
            
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dashboard UI with tabs and widgets."""
        layout = QVBoxLayout(self)
        
        # Main title
        main_title = QLabel("🚀 DjAlfin Analytics Dashboard")
        main_title.setFont(QFont("Arial", 20, QFont.Bold))
        main_title.setStyleSheet("color: #4CAF50; margin-bottom: 15px;")
        main_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(main_title)
        
        # Subtitle with performance info and backend status            
        subtitle = QLabel(f"Ultra-fast analytics powered by {self.backend_info}")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #03DAC6; margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Warning message if matplotlib issues
        if not matplotlib_available:
            warning = QLabel("⚠️ Matplotlib unavailable - Using text-based analytics mode")
            warning.setFont(QFont("Arial", 10))
            warning.setStyleSheet("color: #ff6b6b; margin-bottom: 10px;")
            warning.setAlignment(Qt.AlignCenter)
            layout.addWidget(warning)
        
        # Simple analytics display for now
        self.analytics_text = QTextEdit()
        self.analytics_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.analytics_text)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh Analytics")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_analytics)
        
        refresh_layout.addWidget(self.refresh_btn)
        layout.addLayout(refresh_layout)
        
        # Status bar
        self.status_label = QLabel("💾 Analytics ready")
        self.status_label.setStyleSheet("color: #03DAC6; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Load initial data
        self.refresh_analytics()
        
    def refresh_analytics(self):
        """Refresh analytics data and display results."""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("🔄 Loading...")
        self.status_label.setText("🔄 Loading analytics...")
        
        try:
            # Get analytics data
            overview = get_library_overview()
            bpm_analysis = analyze_bpm_patterns()
            
            # Format display text
            text = f"""
🚀 DJALFIN ANALYTICS DASHBOARD
===============================================

📊 LIBRARY OVERVIEW:
• Total Tracks: {overview.get('total_tracks', 0)}
• Total Artists: {overview.get('total_artists', 0)}
• Total Albums: {overview.get('total_albums', 0)}
• Average BPM: {overview.get('avg_bpm', 0):.1f}
• Library Duration: {overview.get('total_duration_hours', 0):.1f} hours
• Average Energy: {overview.get('avg_energy', 0):.1f}/10

🎵 BPM ANALYSIS:
• Min BPM: {bpm_analysis.get('min_bpm', 'N/A')}
• Max BPM: {bpm_analysis.get('max_bpm', 'N/A')}
• Average BPM: {bpm_analysis.get('avg_bpm', 0):.1f}
• Median BPM: {bpm_analysis.get('median_bpm', 0):.1f}
• Standard Deviation: {bpm_analysis.get('std_bpm', 0):.1f}

📈 BPM RANGE DISTRIBUTION:
"""
            
            ranges = bpm_analysis.get('bpm_ranges', {})
            for range_name, count in ranges.items():
                if count > 0:
                    text += f"• {range_name}: {count} tracks\n"
            
            text += "\n🎧 GENRE-BPM ANALYSIS:\n"
            genre_bpm = bpm_analysis.get('genre_bpm_avg', {})
            for genre, avg_bpm in list(genre_bpm.items())[:8]:
                text += f"• {genre}: {avg_bpm:.1f} BPM\n"
            
            text += f"""

🎯 DJ INSIGHTS:
• Most tracks suitable for {self._get_mixing_style(bpm_analysis)} style
• BPM variety: {self._get_variety_assessment(bpm_analysis)}
• Library is optimized for professional DJ use

⚡ PERFORMANCE STATS:
• Analytics Engine: PyArrow + Polars
• Backend Status: {self.backend_info}
• Last Updated: {datetime.now().strftime('%H:%M:%S')}
"""
            
            self.analytics_text.setPlainText(text)
            self.status_label.setText("✅ Analytics updated successfully")
            
        except Exception as e:
            error_text = f"""
❌ ANALYTICS ERROR

Error loading analytics data: {str(e)}

This may be due to:
• PyArrow/matplotlib compatibility issues
• Database connection problems
• Missing track data

Please check the console for detailed error information.
"""
            self.analytics_text.setPlainText(error_text)
            self.status_label.setText(f"❌ Error: {str(e)}")
            print(f"Analytics error: {e}")
        
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 Refresh Analytics")
    
    def _get_mixing_style(self, bpm_data: Dict) -> str:
        """Suggest mixing style based on BPM distribution."""
        avg_bpm = bpm_data.get('avg_bpm', 120)
        if avg_bpm < 100:
            return "ambient/downtempo"
        elif avg_bpm < 120:
            return "house/deep house"
        elif avg_bpm < 140:
            return "progressive/tech house"
        else:
            return "techno/trance"
            
    def _get_variety_assessment(self, bpm_data: Dict) -> str:
        """Assess BPM variety in library."""
        std_bpm = bpm_data.get('std_bpm', 0)
        if std_bpm < 10:
            return "Low variety (focused genre collection)"
        elif std_bpm < 20:
            return "Moderate variety (good for mixed sets)"
        else:
            return "High variety (excellent for diverse sets)"


if __name__ == "__main__":
    # Test the analytics dashboard
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Apply dark theme
    app.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
            color: white;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 20px;
            padding: 0 10px 0 10px;
        }
    """)
    
    dashboard = AnalyticsDashboard()
    dashboard.show()
    
    sys.exit(app.exec())