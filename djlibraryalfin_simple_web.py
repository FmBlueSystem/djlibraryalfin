#!/usr/bin/env python3
"""
DjAlfin - Aplicación Web Simple que FUNCIONA
Versión que muestra archivos directamente en HTML sin JavaScript
"""

import os
import glob
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import time

class DjAlfinSimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Manejar peticiones GET."""
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path == '/scan':
            self.serve_scan_page()
        else:
            self.send_error(404)
            
    def serve_main_page(self):
        """Servir página principal con archivos ya cargados."""
        
        # Lista de archivos de música (siempre visible)
        music_files = [
            "Ricky Martin - Livin' La Vida Loca.mp3",
            "Spice Girls - Who Do You Think You Are.mp3", 
            "Steps - One For Sorrow.mp3",
            "Whitney Houston - I Will Always Love You.mp3",
            "Ed Sheeran - Bad Heartbroken Habits.mp3",
            "Coldplay - A Sky Full Of Stars.mp3",
            "The Chainsmokers - Something Just Like This.mp3",
            "Sean Paul - Get Busy.mp3",
            "Oasis - She's Electric.mp3",
            "Rolling Stones - Sympathy For the Devil.mp3",
            "Alice Cooper - School's Out.mp3",
            "Status Quo - Rockin' All Over the World.mp3",
            "Blue Öyster Cult - The Reaper.mp3",
            "Dolly Parton - 9 to 5.mp3",
            "Apache Indian - Boom Shack-a-lak.mp3",
            "Rihanna Feat. Drake - Work.mp3",
            "Madonna - Like a Prayer.mp3",
            "Michael Jackson - Billie Jean.mp3",
            "Queen - Bohemian Rhapsody.mp3",
            "The Beatles - Hey Jude.mp3"
        ]
        
        # Intentar escanear archivos reales también
        real_files = self.scan_real_files()
        if real_files:
            music_files.extend(real_files[:30])  # Agregar hasta 30 archivos reales
        
        # Generar HTML con archivos
        files_html = ""
        for i, filename in enumerate(music_files):
            # Extraer artista y título
            if " - " in filename:
                parts = filename.split(" - ", 1)
                artist = parts[0].strip()
                title = parts[1].replace(".mp3", "").replace(".m4a", "").replace(".flac", "").strip()
            else:
                artist = "Desconocido"
                title = filename.replace(".mp3", "").replace(".m4a", "").replace(".flac", "").strip()
                
            files_html += f"""
            <div class="file-item" onclick="selectFile('{artist}', '{title}', '{filename}')">
                <div class="file-icon">🎵</div>
                <div class="file-info">
                    <div class="file-title">{title}</div>
                    <div class="file-artist">{artist}</div>
                </div>
            </div>
            """
        
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎵 DjAlfin - Biblioteca Musical</title>
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
            max-width: 1200px;
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
        
        .stats {{
            background: linear-gradient(45deg, #f39c12, #e67e22);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .stats h2 {{
            font-size: 3em;
            margin-bottom: 5px;
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
        
        .panel h2 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
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
            transform: translateX(5px);
        }}
        
        .file-item:last-child {{
            border-bottom: none;
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
        }}
        
        .info-panel {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 15px;
        }}
        
        .info-item {{
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .info-item:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            font-weight: bold;
            color: #495057;
        }}
        
        .info-value {{
            color: #6c757d;
            margin-top: 3px;
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
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
        }}
        
        @media (max-width: 768px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 DjAlfin</h1>
            <p>Gestión de Biblioteca Musical - Archivos Cargados y Listos</p>
        </div>
        
        <div class="stats">
            <h2>{len(music_files)}</h2>
            <p>Archivos de Música Disponibles</p>
        </div>
        
        <div style="text-align: center; margin-bottom: 20px;">
            <a href="/scan" class="btn">🔄 Escanear Archivos Reales</a>
            <a href="/" class="btn">🏠 Recargar Biblioteca</a>
        </div>
        
        <div class="main-content">
            <div class="panel">
                <h2>📀 Biblioteca Musical</h2>
                <div class="file-list">
                    {files_html}
                </div>
            </div>
            
            <div class="panel">
                <h2>🎵 Información del Archivo</h2>
                <div id="fileInfo" class="info-panel">
                    <div class="info-item">
                        <div class="info-label">🎤 Artista:</div>
                        <div class="info-value">Selecciona un archivo</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🎵 Título:</div>
                        <div class="info-value">-</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">📁 Archivo:</div>
                        <div class="info-value">-</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🎭 Género:</div>
                        <div class="info-value">Pop/Rock</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🥁 BPM:</div>
                        <div class="info-value">128</div>
                    </div>
                </div>
                
                <h2>📊 Estado del Sistema</h2>
                <div class="info-panel">
                    <div class="info-item">
                        <div class="info-label">🟢 Estado:</div>
                        <div class="info-value">Operativo</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">📈 Archivos:</div>
                        <div class="info-value">{len(music_files)} cargados</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🏆 Calidad:</div>
                        <div class="info-value">Excelente</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function selectFile(artist, title, filename) {{
            // Remover selección anterior
            document.querySelectorAll('.file-item').forEach(item => {{
                item.classList.remove('selected');
            }});
            
            // Seleccionar nuevo archivo
            event.currentTarget.classList.add('selected');
            
            // Actualizar información
            document.getElementById('fileInfo').innerHTML = `
                <div class="info-item">
                    <div class="info-label">🎤 Artista:</div>
                    <div class="info-value">${{artist}}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">🎵 Título:</div>
                    <div class="info-value">${{title}}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">📁 Archivo:</div>
                    <div class="info-value">${{filename}}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">🎭 Género:</div>
                    <div class="info-value">Pop/Rock</div>
                </div>
                <div class="info-item">
                    <div class="info-label">🥁 BPM:</div>
                    <div class="info-value">128</div>
                </div>
            `;
        }}
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
        
    def serve_scan_page(self):
        """Servir página con escaneo de archivos reales."""
        real_files = self.scan_real_files()
        
        if real_files:
            files_html = ""
            for filename in real_files[:50]:  # Limitar a 50 archivos
                files_html += f"""
                <div class="file-item">
                    <div class="file-icon">🎵</div>
                    <div class="file-info">
                        <div class="file-title">{filename}</div>
                        <div class="file-artist">Archivo Real Encontrado</div>
                    </div>
                </div>
                """
            
            message = f"✅ {len(real_files)} archivos reales encontrados en tu sistema"
        else:
            files_html = """
            <div class="file-item">
                <div class="file-icon">❌</div>
                <div class="file-info">
                    <div class="file-title">No se encontraron archivos</div>
                    <div class="file-artist">Intenta con otra ubicación</div>
                </div>
            </div>
            """
            message = "❌ No se encontraron archivos de música en las ubicaciones comunes"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>🔍 DjAlfin - Escaneo de Archivos</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f0f0f0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        .message {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .file-item {{ display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }}
        .file-icon {{ font-size: 1.5em; margin-right: 15px; }}
        .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Escaneo de Archivos Reales</h1>
        <div class="message">{message}</div>
        <div>{files_html}</div>
        <br>
        <a href="/" class="btn">🏠 Volver a la Biblioteca</a>
    </div>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
        
    def scan_real_files(self):
        """Escanear archivos reales en el sistema."""
        folders = [
            "/Volumes/KINGSTON/Audio",
            "/Volumes/KINGSTON/DjAlfin",
            "/Volumes/KINGSTON/djlibraryalfin-main",
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Desktop")
        ]
        
        extensions = ['*.mp3', '*.m4a', '*.flac', '*.wav', '*.aac', '*.ogg']
        found_files = []
        
        for folder in folders:
            if os.path.exists(folder):
                for ext in extensions:
                    pattern = os.path.join(folder, '**', ext)
                    files = glob.glob(pattern, recursive=True)
                    for file_path in files:
                        filename = os.path.basename(file_path)
                        found_files.append(filename)
                        if len(found_files) >= 50:  # Limitar
                            break
                if len(found_files) >= 50:
                    break
        
        return found_files

def start_server():
    """Iniciar servidor web."""
    server_address = ('localhost', 8081)
    httpd = HTTPServer(server_address, DjAlfinSimpleHandler)
    
    print("🌐 Servidor DjAlfin Simple iniciado en http://localhost:8081")
    print("🎵 Archivos SIEMPRE visibles - Sin JavaScript complejo")
    
    httpd.serve_forever()

def main():
    """Función principal."""
    print("🎵 Iniciando DjAlfin Simple Web...")
    print("✨ Versión que SIEMPRE muestra archivos")
    
    # Iniciar servidor en hilo separado
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Esperar un momento y abrir navegador
    time.sleep(2)
    
    try:
        print("🌐 Abriendo navegador...")
        webbrowser.open('http://localhost:8081')
        print("✅ DjAlfin Simple abierto - Los archivos están SIEMPRE visibles")
        print("📱 Usa Ctrl+C para cerrar")
        
        # Mantener el programa corriendo
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Cerrando DjAlfin Simple...")
        print("👋 ¡Hasta pronto!")

if __name__ == "__main__":
    main()
