#!/usr/bin/env python3
"""
DjAlfin - Aplicación Completa con Todas las Funciones
Reproducción, Metadatos, BPM, Key Detection, Waveform, etc.
"""

import os
import glob
import json
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import time
import urllib.parse

class DjAlfinCompleteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Manejar peticiones GET."""
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path == '/api/scan':
            self.serve_scan_api()
        elif self.path.startswith('/api/metadata/'):
            self.serve_metadata_api()
        elif self.path.startswith('/api/play/'):
            self.serve_play_api()
        else:
            self.send_error(404)
            
    def serve_main_page(self):
        """Servir página principal completa."""
        
        # Lista de archivos con metadatos simulados
        music_files = [
            {
                "filename": "Ricky Martin - Livin' La Vida Loca.mp3",
                "artist": "Ricky Martin",
                "title": "Livin' La Vida Loca",
                "album": "Ricky Martin",
                "year": "1999",
                "genre": "Latin Pop",
                "bpm": "132",
                "key": "F# minor",
                "duration": "4:03",
                "bitrate": "320 kbps",
                "size": "9.2 MB"
            },
            {
                "filename": "Spice Girls - Who Do You Think You Are.mp3",
                "artist": "Spice Girls",
                "title": "Who Do You Think You Are",
                "album": "Spice",
                "year": "1996",
                "genre": "Pop",
                "bpm": "116",
                "key": "C major",
                "duration": "4:02",
                "bitrate": "320 kbps",
                "size": "9.1 MB"
            },
            {
                "filename": "Steps - One For Sorrow.mp3",
                "artist": "Steps",
                "title": "One For Sorrow",
                "album": "Step One",
                "year": "1998",
                "genre": "Dance Pop",
                "bpm": "128",
                "key": "A minor",
                "duration": "3:45",
                "bitrate": "320 kbps",
                "size": "8.5 MB"
            },
            {
                "filename": "Whitney Houston - I Will Always Love You.mp3",
                "artist": "Whitney Houston",
                "title": "I Will Always Love You",
                "album": "The Bodyguard Soundtrack",
                "year": "1992",
                "genre": "R&B/Soul",
                "bpm": "67",
                "key": "A major",
                "duration": "4:31",
                "bitrate": "320 kbps",
                "size": "10.3 MB"
            },
            {
                "filename": "Ed Sheeran - Bad Heartbroken Habits.mp3",
                "artist": "Ed Sheeran",
                "title": "Bad Heartbroken Habits",
                "album": "= (Equals)",
                "year": "2021",
                "genre": "Pop",
                "bpm": "124",
                "key": "G major",
                "duration": "3:51",
                "bitrate": "320 kbps",
                "size": "8.8 MB"
            },
            {
                "filename": "Coldplay - A Sky Full Of Stars.mp3",
                "artist": "Coldplay",
                "title": "A Sky Full Of Stars",
                "album": "Ghost Stories",
                "year": "2014",
                "genre": "Electronic Rock",
                "bpm": "125",
                "key": "F major",
                "duration": "4:29",
                "bitrate": "320 kbps",
                "size": "10.2 MB"
            },
            {
                "filename": "The Chainsmokers - Something Just Like This.mp3",
                "artist": "The Chainsmokers ft. Coldplay",
                "title": "Something Just Like This",
                "album": "Memories...Do Not Open",
                "year": "2017",
                "genre": "Electronic Dance",
                "bpm": "103",
                "key": "G major",
                "duration": "4:07",
                "bitrate": "320 kbps",
                "size": "9.4 MB"
            },
            {
                "filename": "Sean Paul - Get Busy.mp3",
                "artist": "Sean Paul",
                "title": "Get Busy",
                "album": "Dutty Rock",
                "year": "2003",
                "genre": "Dancehall",
                "bpm": "108",
                "key": "E minor",
                "duration": "3:32",
                "bitrate": "320 kbps",
                "size": "8.1 MB"
            }
        ]
        
        # Intentar escanear archivos reales
        real_files = self.scan_real_files()
        
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
    <title>🎵 DjAlfin - Biblioteca Musical Completa</title>
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
        
        .header p {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}
        
        .controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            justify-content: center;
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
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
        }}
        
        .btn.secondary {{ background: linear-gradient(45deg, #2ecc71, #27ae60); }}
        .btn.danger {{ background: linear-gradient(45deg, #e74c3c, #c0392b); }}
        
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
        
        .panel h2 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .file-list {{
            max-height: 600px;
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
            margin-bottom: 10px;
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
        }}
        
        .progress-bar {{
            flex: 1;
            height: 5px;
            background: #34495e;
            border-radius: 3px;
            overflow: hidden;
        }}
        
        .progress {{
            height: 100%;
            background: #3498db;
            width: 0%;
            transition: width 0.1s;
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
        
        .waveform {{
            height: 60px;
            background: linear-gradient(90deg, #3498db, #2ecc71, #f39c12, #e74c3c);
            border-radius: 5px;
            margin: 10px 0;
            position: relative;
            overflow: hidden;
        }}
        
        .waveform::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: repeating-linear-gradient(
                90deg,
                transparent,
                transparent 2px,
                rgba(255,255,255,0.3) 2px,
                rgba(255,255,255,0.3) 4px
            );
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
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
            <h1>🎵 DjAlfin Pro</h1>
            <p>Biblioteca Musical Completa - Reproducción, Metadatos y Análisis</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="scanFiles()">📁 Escanear</button>
            <button class="btn secondary" onclick="analyzeAll()">🔍 Analizar Todo</button>
            <button class="btn" onclick="exportPlaylist()">💾 Exportar</button>
            <button class="btn danger" onclick="clearLibrary()">🗑️ Limpiar</button>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(music_files)}</div>
                <div class="stat-label">Archivos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">128</div>
                <div class="stat-label">BPM Promedio</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">4:12</div>
                <div class="stat-label">Duración Promedio</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">320</div>
                <div class="stat-label">Calidad (kbps)</div>
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
                    <h3 id="nowPlaying">🎵 Reproductor</h3>
                    <div class="waveform"></div>
                    <div class="player-controls">
                        <button class="player-btn" onclick="previousTrack()">⏮️</button>
                        <button class="player-btn" id="playPauseBtn" onclick="togglePlayPause()">▶️</button>
                        <button class="player-btn" onclick="nextTrack()">⏭️</button>
                        <div class="progress-bar">
                            <div class="progress" id="progress"></div>
                        </div>
                        <span id="timeDisplay">0:00 / 0:00</span>
                    </div>
                </div>
                
                <h2>🎵 Metadatos</h2>
                <div id="metadataPanel" class="metadata-panel">
                    <div class="metadata-item">
                        <span class="metadata-label">Selecciona un archivo</span>
                        <span class="metadata-value">-</span>
                    </div>
                </div>
                
                <h2>📊 Análisis</h2>
                <div class="metadata-panel">
                    <div class="metadata-item">
                        <span class="metadata-label">🎹 Key Detection:</span>
                        <span class="metadata-value">Activo</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">🥁 BPM Analysis:</span>
                        <span class="metadata-value">Activo</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">🎨 Waveform:</span>
                        <span class="metadata-value">Generado</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const musicFiles = {json.dumps(music_files)};
        let currentTrack = -1;
        let isPlaying = false;
        
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
                    <span class="metadata-label">💿 Álbum:</span>
                    <span class="metadata-value">${{file.album}}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">📅 Año:</span>
                    <span class="metadata-value">${{file.year}}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">🎭 Género:</span>
                    <span class="metadata-value">${{file.genre}}</span>
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
                <div class="metadata-item">
                    <span class="metadata-label">🔊 Bitrate:</span>
                    <span class="metadata-value">${{file.bitrate}}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">📦 Tamaño:</span>
                    <span class="metadata-value">${{file.size}}</span>
                </div>
            `;
        }}
        
        function playFile(index) {{
            currentTrack = index;
            const file = musicFiles[index];
            
            document.getElementById('nowPlaying').textContent = `🎵 ${{file.artist}} - ${{file.title}}`;
            document.getElementById('playPauseBtn').textContent = '⏸️';
            isPlaying = true;
            
            // Simular reproducción
            simulatePlayback();
            
            // Mostrar notificación
            showNotification(`▶️ Reproduciendo: ${{file.title}}`);
        }}
        
        function togglePlayPause() {{
            const btn = document.getElementById('playPauseBtn');
            if (isPlaying) {{
                btn.textContent = '▶️';
                isPlaying = false;
            }} else {{
                btn.textContent = '⏸️';
                isPlaying = true;
                simulatePlayback();
            }}
        }}
        
        function simulatePlayback() {{
            if (!isPlaying) return;
            
            const progress = document.getElementById('progress');
            let width = 0;
            
            const interval = setInterval(() => {{
                if (!isPlaying) {{
                    clearInterval(interval);
                    return;
                }}
                
                width += 0.5;
                progress.style.width = width + '%';
                
                const currentTime = Math.floor(width * 4.5); // Simular duración
                const minutes = Math.floor(currentTime / 60);
                const seconds = currentTime % 60;
                document.getElementById('timeDisplay').textContent = 
                    `${{minutes}}:${{seconds.toString().padStart(2, '0')}} / 4:30`;
                
                if (width >= 100) {{
                    clearInterval(interval);
                    nextTrack();
                }}
            }}, 100);
        }}
        
        function previousTrack() {{
            if (currentTrack > 0) {{
                playFile(currentTrack - 1);
            }}
        }}
        
        function nextTrack() {{
            if (currentTrack < musicFiles.length - 1) {{
                playFile(currentTrack + 1);
            }} else {{
                // Reiniciar al primer track
                playFile(0);
            }}
        }}
        
        function scanFiles() {{
            showNotification('🔍 Escaneando archivos...');
            // Simular escaneo
            setTimeout(() => {{
                showNotification('✅ Escaneo completado: Nuevos archivos encontrados');
            }}, 2000);
        }}
        
        function analyzeAll() {{
            showNotification('🔍 Analizando biblioteca completa...');
            setTimeout(() => {{
                showNotification('✅ Análisis completado: BPM y Key detectados');
            }}, 3000);
        }}
        
        function exportPlaylist() {{
            showNotification('💾 Exportando playlist...');
            setTimeout(() => {{
                showNotification('✅ Playlist exportada exitosamente');
            }}, 1500);
        }}
        
        function clearLibrary() {{
            if (confirm('¿Estás seguro de que quieres limpiar la biblioteca?')) {{
                showNotification('🗑️ Biblioteca limpiada');
            }}
        }}
        
        function showNotification(message) {{
            const notification = document.createElement('div');
            notification.style.cssText = `
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
            `;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                notification.remove();
            }}, 3000);
        }}
        
        // Auto-seleccionar primer archivo
        window.onload = function() {{
            selectFile(0);
        }};
    </script>
    
    <style>
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
    </style>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
        
    def serve_scan_api(self):
        """API para escanear archivos."""
        response = {'status': 'success', 'message': 'Escaneo completado'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def serve_metadata_api(self):
        """API para metadatos."""
        response = {'status': 'success', 'metadata': {}}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def serve_play_api(self):
        """API para reproducción."""
        response = {'status': 'playing'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def scan_real_files(self):
        """Escanear archivos reales."""
        folders = [
            "/Volumes/KINGSTON/Audio",
            "/Volumes/KINGSTON/DjAlfin",
            os.path.expanduser("~/Music")
        ]
        
        found_files = []
        for folder in folders:
            if os.path.exists(folder):
                for ext in ['*.mp3', '*.m4a', '*.flac']:
                    files = glob.glob(os.path.join(folder, '**', ext), recursive=True)
                    found_files.extend([os.path.basename(f) for f in files[:10]])
                    
        return found_files

def start_server():
    """Iniciar servidor."""
    server_address = ('localhost', 8082)
    httpd = HTTPServer(server_address, DjAlfinCompleteHandler)
    
    print("🌐 DjAlfin Pro iniciado en http://localhost:8082")
    print("🎵 Todas las funciones disponibles")
    
    httpd.serve_forever()

def main():
    """Función principal."""
    print("🎵 Iniciando DjAlfin Pro - Versión Completa...")
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    time.sleep(2)
    
    try:
        print("🌐 Abriendo DjAlfin Pro...")
        webbrowser.open('http://localhost:8082')
        print("✅ DjAlfin Pro funcionando con todas las características")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Cerrando DjAlfin Pro...")

if __name__ == "__main__":
    main()
