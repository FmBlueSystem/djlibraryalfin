#!/usr/bin/env python3
"""
DjAlfin - Reproductor Real de Archivos
Versión que reproduce archivos de audio reales
"""

import os
import glob
import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import time
import urllib.parse

class DjAlfinPlayerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Manejar peticiones GET."""
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path.startswith('/audio/'):
            self.serve_audio_file()
        elif self.path == '/api/scan':
            self.serve_scan_api()
        else:
            self.send_error(404)
            
    def serve_main_page(self):
        """Servir página principal con reproductor real."""
        
        # Escanear archivos reales
        real_files = self.scan_real_files()
        
        # Si no hay archivos reales, usar archivos de ejemplo
        if not real_files:
            music_files = [
                {
                    "filename": "sample_track_1.mp3",
                    "artist": "Artista de Ejemplo",
                    "title": "Canción de Prueba 1",
                    "path": "/audio/sample1",
                    "duration": "3:45",
                    "bpm": "128",
                    "key": "C major"
                },
                {
                    "filename": "sample_track_2.mp3", 
                    "artist": "Artista de Ejemplo",
                    "title": "Canción de Prueba 2",
                    "path": "/audio/sample2",
                    "duration": "4:12",
                    "bpm": "120",
                    "key": "G major"
                }
            ]
        else:
            music_files = []
            for i, file_path in enumerate(real_files[:20]):  # Limitar a 20 archivos
                filename = os.path.basename(file_path)
                
                # Extraer artista y título del nombre del archivo
                if " - " in filename:
                    parts = filename.split(" - ", 1)
                    artist = parts[0].strip()
                    title = parts[1].replace(".mp3", "").replace(".m4a", "").replace(".flac", "").strip()
                else:
                    artist = "Artista Desconocido"
                    title = filename.replace(".mp3", "").replace(".m4a", "").replace(".flac", "").strip()
                
                music_files.append({
                    "filename": filename,
                    "artist": artist,
                    "title": title,
                    "path": f"/audio/{i}",
                    "real_path": file_path,
                    "duration": "0:00",
                    "bpm": "128",
                    "key": "C major"
                })
        
        # Generar HTML de archivos
        files_html = ""
        for i, file_data in enumerate(music_files):
            files_html += f"""
            <div class="file-item" onclick="selectFile({i})">
                <div class="file-icon">🎵</div>
                <div class="file-info">
                    <div class="file-title">{file_data['title']}</div>
                    <div class="file-artist">{file_data['artist']}</div>
                    <div class="file-meta">{file_data['bpm']} BPM • {file_data['key']} • {file_data['duration']}</div>
                </div>
                <div class="file-actions">
                    <button class="play-btn" onclick="playFile({i}); event.stopPropagation();">▶️</button>
                    <button class="info-btn" onclick="showMetadata({i}); event.stopPropagation();">ℹ️</button>
                </div>
            </div>
            """
        
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎵 DjAlfin - Reproductor Real</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .main-content {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }}
        
        .panel {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        .file-list {{
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid #ecf0f1;
            border-radius: 8px;
        }}
        
        .file-item {{
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .file-item:hover {{
            background: #f8f9fa;
        }}
        
        .file-item.selected {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }}
        
        .file-icon {{
            font-size: 1.5em;
            margin-right: 15px;
        }}
        
        .file-info {{
            flex: 1;
        }}
        
        .file-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 3px;
        }}
        
        .file-artist {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 3px;
        }}
        
        .file-meta {{
            color: #95a5a6;
            font-size: 0.8em;
        }}
        
        .file-actions {{
            display: flex;
            gap: 5px;
        }}
        
        .play-btn, .info-btn {{
            background: none;
            border: none;
            font-size: 1.2em;
            cursor: pointer;
            padding: 5px;
            border-radius: 5px;
            transition: background 0.2s;
        }}
        
        .play-btn:hover {{
            background: #e8f5e8;
        }}
        
        .info-btn:hover {{
            background: #e3f2fd;
        }}
        
        .player {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        
        .player h3 {{
            margin-bottom: 15px;
            font-size: 1.1em;
        }}
        
        .audio-player {{
            width: 100%;
            margin-bottom: 15px;
        }}
        
        .player-controls {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .player-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1.1em;
        }}
        
        .player-btn:hover {{
            background: #2980b9;
        }}
        
        .volume-control {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .volume-slider {{
            width: 80px;
        }}
        
        .metadata-panel {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        
        .metadata-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .metadata-item:last-child {{
            border-bottom: none;
        }}
        
        .metadata-label {{
            font-weight: bold;
            color: #495057;
        }}
        
        .metadata-value {{
            color: #6c757d;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(45deg, #f39c12, #e67e22);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .controls {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .btn {{
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            margin: 0 5px;
            transition: all 0.3s ease;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
        }}
        
        .notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2c3e50;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        @media (max-width: 768px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 DjAlfin Player</h1>
            <p>Reproductor de Audio Real - {len(music_files)} archivos disponibles</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="scanFiles()">📁 Escanear Nuevos Archivos</button>
            <button class="btn" onclick="refreshLibrary()">🔄 Actualizar Biblioteca</button>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(music_files)}</div>
                <div class="stat-label">Archivos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{'Real' if real_files else 'Demo'}</div>
                <div class="stat-label">Modo</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="panel">
                <h2>📀 Biblioteca Musical</h2>
                <div class="file-list">
                    {files_html}
                </div>
            </div>
            
            <div class="panel">
                <div class="player">
                    <h3 id="nowPlaying">🎵 Selecciona un archivo para reproducir</h3>
                    <audio id="audioPlayer" class="audio-player" controls style="display: none;">
                        Tu navegador no soporta el elemento de audio.
                    </audio>
                    <div class="player-controls">
                        <button class="player-btn" onclick="previousTrack()">⏮️</button>
                        <button class="player-btn" id="playPauseBtn" onclick="togglePlayPause()">▶️</button>
                        <button class="player-btn" onclick="nextTrack()">⏭️</button>
                        <div class="volume-control">
                            <span>🔊</span>
                            <input type="range" class="volume-slider" id="volumeSlider" min="0" max="100" value="50" onchange="setVolume(this.value)">
                        </div>
                    </div>
                </div>
                
                <h2>🎵 Información del Archivo</h2>
                <div id="metadataPanel" class="metadata-panel">
                    <div class="metadata-item">
                        <span class="metadata-label">Selecciona un archivo</span>
                        <span class="metadata-value">-</span>
                    </div>
                </div>
                
                <h2>📊 Estado del Reproductor</h2>
                <div class="metadata-panel">
                    <div class="metadata-item">
                        <span class="metadata-label">🎵 Estado:</span>
                        <span class="metadata-value" id="playerStatus">Detenido</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">🔊 Volumen:</span>
                        <span class="metadata-value" id="volumeDisplay">50%</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">📁 Archivos:</span>
                        <span class="metadata-value">{len(music_files)} cargados</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const musicFiles = {json.dumps(music_files)};
        let currentTrack = -1;
        const audioPlayer = document.getElementById('audioPlayer');
        
        function selectFile(index) {{
            // Remover selección anterior
            document.querySelectorAll('.file-item').forEach(item => {{
                item.classList.remove('selected');
            }});
            
            // Seleccionar nuevo archivo
            document.querySelectorAll('.file-item')[index].classList.add('selected');
            
            // Mostrar metadatos
            showMetadata(index);
        }}
        
        function showMetadata(index) {{
            const file = musicFiles[index];
            const panel = document.getElementById('metadataPanel');
            
            panel.innerHTML = `
                <div class="metadata-item">
                    <span class="metadata-label">🎤 Artista:</span>
                    <span class="metadata-value">${{file.artist}}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">🎵 Título:</span>
                    <span class="metadata-value">${{file.title}}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">📁 Archivo:</span>
                    <span class="metadata-value">${{file.filename}}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">🥁 BPM:</span>
                    <span class="metadata-value">${{file.bpm}}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">🎹 Key:</span>
                    <span class="metadata-value">${{file.key}}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">⏱️ Duración:</span>
                    <span class="metadata-value">${{file.duration}}</span>
                </div>
            `;
        }}
        
        function playFile(index) {{
            currentTrack = index;
            const file = musicFiles[index];
            
            // Configurar reproductor de audio
            audioPlayer.src = file.path;
            audioPlayer.style.display = 'block';
            
            // Actualizar interfaz
            document.getElementById('nowPlaying').textContent = `🎵 ${{file.artist}} - ${{file.title}}`;
            document.getElementById('playPauseBtn').textContent = '⏸️';
            document.getElementById('playerStatus').textContent = 'Reproduciendo';
            
            // Reproducir
            audioPlayer.play().then(() => {{
                showNotification(`▶️ Reproduciendo: ${{file.title}}`);
            }}).catch(error => {{
                console.error('Error reproduciendo:', error);
                showNotification(`❌ Error: No se puede reproducir ${{file.title}}`);
                document.getElementById('playerStatus').textContent = 'Error';
            }});
            
            // Seleccionar archivo
            selectFile(index);
        }}
        
        function togglePlayPause() {{
            if (audioPlayer.paused) {{
                audioPlayer.play();
                document.getElementById('playPauseBtn').textContent = '⏸️';
                document.getElementById('playerStatus').textContent = 'Reproduciendo';
            }} else {{
                audioPlayer.pause();
                document.getElementById('playPauseBtn').textContent = '▶️';
                document.getElementById('playerStatus').textContent = 'Pausado';
            }}
        }}
        
        function previousTrack() {{
            if (currentTrack > 0) {{
                playFile(currentTrack - 1);
            }}
        }}
        
        function nextTrack() {{
            if (currentTrack < musicFiles.length - 1) {{
                playFile(currentTrack + 1);
            }}
        }}
        
        function setVolume(value) {{
            audioPlayer.volume = value / 100;
            document.getElementById('volumeDisplay').textContent = value + '%';
        }}
        
        function scanFiles() {{
            showNotification('🔍 Escaneando nuevos archivos...');
            fetch('/api/scan')
                .then(response => response.json())
                .then(data => {{
                    showNotification('✅ Escaneo completado');
                }})
                .catch(error => {{
                    showNotification('❌ Error en el escaneo');
                }});
        }}
        
        function refreshLibrary() {{
            location.reload();
        }}
        
        function showNotification(message) {{
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                notification.remove();
            }}, 3000);
        }}
        
        // Eventos del reproductor de audio
        audioPlayer.addEventListener('ended', () => {{
            document.getElementById('playPauseBtn').textContent = '▶️';
            document.getElementById('playerStatus').textContent = 'Finalizado';
            nextTrack();
        }});
        
        audioPlayer.addEventListener('loadstart', () => {{
            document.getElementById('playerStatus').textContent = 'Cargando...';
        }});
        
        audioPlayer.addEventListener('canplay', () => {{
            document.getElementById('playerStatus').textContent = 'Listo';
        }});
        
        // Configurar volumen inicial
        setVolume(50);
        
        // Auto-seleccionar primer archivo
        if (musicFiles.length > 0) {{
            selectFile(0);
        }}
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
        
    def serve_audio_file(self):
        """Servir archivos de audio."""
        # Extraer índice del archivo de la URL
        try:
            file_index = int(self.path.split('/')[-1])
            real_files = self.scan_real_files()
            
            if real_files and file_index < len(real_files):
                file_path = real_files[file_index]
                
                if os.path.exists(file_path):
                    # Determinar tipo MIME
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if not mime_type:
                        mime_type = 'audio/mpeg'
                    
                    # Leer y servir archivo
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-type', mime_type)
                    self.send_header('Content-length', str(len(content)))
                    self.send_header('Accept-Ranges', 'bytes')
                    self.end_headers()
                    self.wfile.write(content)
                    return
                    
        except (ValueError, IndexError):
            pass
        
        # Si no se encuentra el archivo, servir audio de ejemplo (silencio)
        self.send_response(404)
        self.end_headers()
        
    def serve_scan_api(self):
        """API para escanear archivos."""
        real_files = self.scan_real_files()
        response = {
            'status': 'success', 
            'files_found': len(real_files),
            'message': f'Encontrados {len(real_files)} archivos'
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def scan_real_files(self):
        """Escanear archivos reales en el sistema."""
        folders = [
            "/Volumes/KINGSTON/Audio",
            "/Volumes/KINGSTON/DjAlfin", 
            "/Volumes/KINGSTON/djlibraryalfin-main",
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads")
        ]
        
        extensions = ['*.mp3', '*.m4a', '*.flac', '*.wav', '*.aac']
        found_files = []
        
        for folder in folders:
            if os.path.exists(folder):
                for ext in extensions:
                    pattern = os.path.join(folder, '**', ext)
                    files = glob.glob(pattern, recursive=True)
                    found_files.extend(files)
                    
                    # Limitar para rendimiento
                    if len(found_files) >= 50:
                        break
                        
                if len(found_files) >= 50:
                    break
        
        return found_files

def start_server():
    """Iniciar servidor."""
    server_address = ('localhost', 8083)
    httpd = HTTPServer(server_address, DjAlfinPlayerHandler)
    
    print("🌐 DjAlfin Player iniciado en http://localhost:8083")
    print("🎵 Reproductor de audio real funcionando")
    
    httpd.serve_forever()

def main():
    """Función principal."""
    print("🎵 Iniciando DjAlfin Player...")
    print("🔊 Reproductor de archivos de audio real")
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    time.sleep(2)
    
    try:
        print("🌐 Abriendo reproductor...")
        webbrowser.open('http://localhost:8083')
        print("✅ DjAlfin Player listo para reproducir archivos")
        print("📱 Usa Ctrl+C para cerrar")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Cerrando DjAlfin Player...")

if __name__ == "__main__":
    main()
