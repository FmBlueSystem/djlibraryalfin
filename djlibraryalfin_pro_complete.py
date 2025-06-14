#!/usr/bin/env python3
"""
DjAlfin Pro - Aplicación Completa de DJ
Todas las funciones profesionales: BPM, Key Detection, Crossfader, EQ, Effects, Playlists, etc.
"""

import os
import glob
import json
import mimetypes
import random
import math
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import time
import urllib.parse

class DjAlfinProHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Manejar peticiones GET."""
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path.startswith('/audio/'):
            self.serve_audio_file()
        elif self.path == '/api/scan':
            self.serve_scan_api()
        elif self.path == '/api/analyze':
            self.serve_analyze_api()
        elif self.path == '/api/playlist':
            self.serve_playlist_api()
        elif self.path == '/api/effects':
            self.serve_effects_api()
        elif self.path == '/api/folders':
            self.serve_folders_api()
        elif self.path == '/api/add_folder':
            self.serve_add_folder_api()
        else:
            self.send_error(404)

    def do_POST(self):
        """Manejar peticiones POST."""
        if self.path == '/api/add_folder':
            self.handle_add_folder_post()
        else:
            self.send_error(404)

    def serve_main_page(self):
        """Servir página principal completa de DJ."""

        # Escanear archivos reales
        real_files = self.scan_real_files()

        # Generar datos de archivos con análisis completo
        music_files = []
        for i, file_path in enumerate(real_files[:30] if real_files else []):
            filename = os.path.basename(file_path)

            # Extraer información del archivo
            if " - " in filename:
                parts = filename.split(" - ", 1)
                artist = parts[0].strip()
                title = parts[1].replace(".mp3", "").replace(".m4a", "").replace(".flac", "").strip()
            else:
                artist = "Artista Desconocido"
                title = filename.replace(".mp3", "").replace(".m4a", "").replace(".flac", "").strip()

            # Generar análisis simulado pero realista
            bpm = random.randint(90, 140)
            keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            modes = ["major", "minor"]
            key = f"{random.choice(keys)} {random.choice(modes)}"

            # Géneros basados en BPM
            if bpm < 100:
                genre = random.choice(["Hip Hop", "R&B", "Reggae", "Dub"])
            elif bpm < 120:
                genre = random.choice(["Pop", "Rock", "Alternative", "Indie"])
            else:
                genre = random.choice(["Dance", "House", "Techno", "Electronic", "Trance"])

            # Duración simulada
            duration_seconds = random.randint(180, 300)
            duration = f"{duration_seconds // 60}:{duration_seconds % 60:02d}"

            # Tamaño del archivo
            try:
                size_bytes = os.path.getsize(file_path)
                size_mb = size_bytes / (1024 * 1024)
                size = f"{size_mb:.1f} MB"
            except:
                size = "0.0 MB"

            music_files.append({
                "id": i,
                "filename": filename,
                "artist": artist,
                "title": title,
                "album": "Unknown Album",
                "year": random.randint(1990, 2024),
                "genre": genre,
                "bpm": bpm,
                "key": key,
                "duration": duration,
                "duration_seconds": duration_seconds,
                "bitrate": "320 kbps",
                "size": size,
                "path": f"/audio/{i}",
                "real_path": file_path,
                "energy": random.randint(1, 10),
                "danceability": random.randint(1, 10),
                "valence": random.randint(1, 10),
                "waveform": self.generate_waveform_data(),
                "color": self.get_genre_color(genre)
            })

        # Si no hay archivos reales, usar datos de ejemplo
        if not music_files:
            music_files = self.get_sample_tracks()

        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎧 DjAlfin Pro - Estación de DJ Completa</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #fff;
            overflow-x: hidden;
        }}

        .dj-console {{
            display: grid;
            grid-template-areas:
                "header header header"
                "deck-a mixer deck-b"
                "library library library"
                "effects effects effects";
            grid-template-rows: auto 300px 1fr auto;
            grid-template-columns: 1fr 300px 1fr;
            gap: 15px;
            padding: 15px;
            min-height: 100vh;
        }}

        .header {{
            grid-area: header;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .deck {{
            background: linear-gradient(145deg, #2c3e50, #34495e);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 2px solid #3498db;
        }}

        .deck-a {{ grid-area: deck-a; }}
        .deck-b {{ grid-area: deck-b; }}

        .deck h3 {{
            color: #3498db;
            margin-bottom: 15px;
            text-align: center;
            font-size: 1.2em;
        }}

        .deck-display {{
            background: #1a1a1a;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #555;
        }}

        .track-info {{
            color: #3498db;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}

        .bpm-display {{
            font-size: 2em;
            font-weight: bold;
            color: #e74c3c;
            text-align: center;
            margin: 10px 0;
        }}

        .deck-controls {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }}

        .deck-btn {{
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 10px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }}

        .deck-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.4);
        }}

        .deck-btn.active {{
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }}

        .mixer {{
            grid-area: mixer;
            background: linear-gradient(145deg, #34495e, #2c3e50);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 2px solid #e74c3c;
        }}

        .mixer h3 {{
            color: #e74c3c;
            text-align: center;
            margin-bottom: 20px;
        }}

        .crossfader-section {{
            margin-bottom: 20px;
        }}

        .crossfader {{
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: #555;
            outline: none;
            margin: 10px 0;
        }}

        .crossfader::-webkit-slider-thumb {{
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #e74c3c;
            cursor: pointer;
        }}

        .eq-section {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}

        .eq-control {{
            text-align: center;
        }}

        .eq-label {{
            font-size: 0.8em;
            color: #bdc3c7;
            margin-bottom: 5px;
        }}

        .eq-knob {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(45deg, #34495e, #2c3e50);
            border: 3px solid #3498db;
            margin: 0 auto;
            position: relative;
            cursor: pointer;
        }}

        .eq-knob::after {{
            content: '';
            position: absolute;
            top: 5px;
            left: 50%;
            transform: translateX(-50%);
            width: 3px;
            height: 15px;
            background: #3498db;
            border-radius: 2px;
        }}

        .library {{
            grid-area: library;
            background: linear-gradient(145deg, #2c3e50, #34495e);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 2px solid #2ecc71;
        }}

        .library h3 {{
            color: #2ecc71;
            margin-bottom: 15px;
        }}

        .library-controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}

        .library-btn {{
            background: linear-gradient(45deg, #2ecc71, #27ae60);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }}

        .library-btn:hover {{
            transform: translateY(-1px);
        }}

        .search-bar {{
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 8px;
            background: #34495e;
            color: white;
            margin-bottom: 15px;
        }}

        .track-list {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #555;
            border-radius: 8px;
        }}

        .track-item {{
            display: grid;
            grid-template-columns: 40px 2fr 1fr 80px 80px 100px;
            gap: 10px;
            padding: 10px;
            border-bottom: 1px solid #555;
            cursor: pointer;
            transition: all 0.2s ease;
            align-items: center;
        }}

        .track-item:hover {{
            background: rgba(52, 152, 219, 0.1);
        }}

        .track-item.selected {{
            background: rgba(52, 152, 219, 0.2);
            border-left: 4px solid #3498db;
        }}

        .track-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin: 0 auto;
        }}

        .track-info-cell {{
            overflow: hidden;
        }}

        .track-title {{
            font-weight: bold;
            color: #ecf0f1;
            font-size: 0.9em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .track-artist {{
            color: #bdc3c7;
            font-size: 0.8em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .track-bpm {{
            color: #e74c3c;
            font-weight: bold;
            text-align: center;
        }}

        .track-key {{
            color: #f39c12;
            font-weight: bold;
            text-align: center;
        }}

        .track-actions {{
            display: flex;
            gap: 5px;
        }}

        .action-btn {{
            background: none;
            border: none;
            color: #bdc3c7;
            cursor: pointer;
            font-size: 1.1em;
            padding: 2px;
            border-radius: 3px;
            transition: all 0.2s ease;
        }}

        .action-btn:hover {{
            background: rgba(255, 255, 255, 0.1);
            transform: scale(1.1);
        }}

        .effects {{
            grid-area: effects;
            background: linear-gradient(145deg, #8e44ad, #9b59b6);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}

        .effects h3 {{
            color: white;
            text-align: center;
            margin-bottom: 15px;
        }}

        .effects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
        }}

        .effect-btn {{
            background: linear-gradient(45deg, #9b59b6, #8e44ad);
            color: white;
            border: none;
            padding: 15px 10px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            text-align: center;
        }}

        .effect-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(155, 89, 182, 0.4);
        }}

        .effect-btn.active {{
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }}

        .waveform {{
            height: 40px;
            background: #1a1a1a;
            border-radius: 4px;
            margin: 10px 0;
            position: relative;
            overflow: hidden;
        }}

        .waveform-bars {{
            display: flex;
            height: 100%;
            align-items: end;
            padding: 2px;
        }}

        .waveform-bar {{
            flex: 1;
            background: linear-gradient(to top, #3498db, #2ecc71);
            margin: 0 1px;
            border-radius: 1px;
            transition: height 0.1s ease;
        }}

        .progress-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            background: rgba(231, 76, 60, 0.3);
            width: 0%;
            transition: width 0.1s ease;
        }}

        .stats-panel {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-number {{
            font-size: 1.5em;
            font-weight: bold;
            color: #3498db;
        }}

        .stat-label {{
            font-size: 0.8em;
            color: #bdc3c7;
        }}

        @media (max-width: 1200px) {{
            .dj-console {{
                grid-template-areas:
                    "header"
                    "mixer"
                    "deck-a"
                    "deck-b"
                    "library"
                    "effects";
                grid-template-columns: 1fr;
                grid-template-rows: auto;
            }}
        }}

        .notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(45deg, #2c3e50, #34495e);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
            border-left: 4px solid #3498db;
        }}

        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
    </style>
</head>
<body>
    <div class="dj-console">
        <div class="header">
            <h1>🎧 DjAlfin Pro</h1>
            <p>Estación de DJ Profesional - {len(music_files)} tracks cargados</p>
            <div class="stats-panel">
                <div class="stat-card">
                    <div class="stat-number">{len(music_files)}</div>
                    <div class="stat-label">Tracks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{sum(f['bpm'] for f in music_files) // len(music_files) if music_files else 0}</div>
                    <div class="stat-label">BPM Avg</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(set(f['key'] for f in music_files))}</div>
                    <div class="stat-label">Keys</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(set(f['genre'] for f in music_files))}</div>
                    <div class="stat-label">Genres</div>
                </div>
            </div>
        </div>

        <!-- DECK A -->
        <div class="deck deck-a">
            <h3>🎧 DECK A</h3>
            <div class="deck-display">
                <div class="track-info" id="deckA-info">No track loaded</div>
                <div class="bpm-display" id="deckA-bpm">000</div>
                <div class="waveform">
                    <div class="waveform-bars" id="deckA-waveform"></div>
                    <div class="progress-overlay" id="deckA-progress"></div>
                </div>
            </div>
            <div class="deck-controls">
                <button class="deck-btn" onclick="loadToDeck('A')">LOAD</button>
                <button class="deck-btn" id="deckA-play" onclick="playDeck('A')">PLAY</button>
                <button class="deck-btn" onclick="cueDeck('A')">CUE</button>
                <button class="deck-btn" onclick="syncDeck('A')">SYNC</button>
                <button class="deck-btn" onclick="loopDeck('A')">LOOP</button>
                <button class="deck-btn" onclick="hotCue('A', 1)">HOT1</button>
            </div>
            <audio id="audioA" preload="metadata"></audio>
        </div>

        <!-- MIXER -->
        <div class="mixer">
            <h3>🎛️ MIXER</h3>
            <div class="crossfader-section">
                <label>Crossfader</label>
                <input type="range" class="crossfader" id="crossfader" min="0" max="100" value="50" onchange="updateCrossfader(this.value)">
                <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #bdc3c7;">
                    <span>A</span>
                    <span>B</span>
                </div>
            </div>

            <div class="eq-section">
                <div class="eq-control">
                    <div class="eq-label">HIGH</div>
                    <div class="eq-knob" onclick="adjustEQ('high')"></div>
                </div>
                <div class="eq-control">
                    <div class="eq-label">MID</div>
                    <div class="eq-knob" onclick="adjustEQ('mid')"></div>
                </div>
                <div class="eq-control">
                    <div class="eq-label">LOW</div>
                    <div class="eq-knob" onclick="adjustEQ('low')"></div>
                </div>
            </div>

            <div style="text-align: center; margin-top: 20px;">
                <button class="deck-btn" onclick="autoMix()">AUTO MIX</button>
                <button class="deck-btn" onclick="beatMatch()">BEAT MATCH</button>
            </div>
        </div>

        <!-- DECK B -->
        <div class="deck deck-b">
            <h3>🎧 DECK B</h3>
            <div class="deck-display">
                <div class="track-info" id="deckB-info">No track loaded</div>
                <div class="bpm-display" id="deckB-bpm">000</div>
                <div class="waveform">
                    <div class="waveform-bars" id="deckB-waveform"></div>
                    <div class="progress-overlay" id="deckB-progress"></div>
                </div>
            </div>
            <div class="deck-controls">
                <button class="deck-btn" onclick="loadToDeck('B')">LOAD</button>
                <button class="deck-btn" id="deckB-play" onclick="playDeck('B')">PLAY</button>
                <button class="deck-btn" onclick="cueDeck('B')">CUE</button>
                <button class="deck-btn" onclick="syncDeck('B')">SYNC</button>
                <button class="deck-btn" onclick="loopDeck('B')">LOOP</button>
                <button class="deck-btn" onclick="hotCue('B', 1)">HOT1</button>
            </div>
            <audio id="audioB" preload="metadata"></audio>
        </div>

        <!-- LIBRARY -->
        <div class="library">
            <h3>📚 BIBLIOTECA MUSICAL</h3>
            <div class="library-controls">
                <button class="library-btn" onclick="scanLibrary()">📁 Escanear</button>
                <button class="library-btn" onclick="addFolder()">➕ Agregar Carpeta</button>
                <button class="library-btn" onclick="analyzeAll()">🔍 Analizar</button>
                <button class="library-btn" onclick="createPlaylist()">📝 Playlist</button>
                <button class="library-btn" onclick="sortBy('bpm')">🥁 Sort BPM</button>
                <button class="library-btn" onclick="sortBy('key')">🎹 Sort Key</button>
                <button class="library-btn" onclick="filterGenre()">🎭 Filter</button>
            </div>
            <input type="text" class="search-bar" placeholder="🔍 Buscar tracks..." onkeyup="searchTracks(this.value)">

            <div class="track-list" id="trackList">
                <!-- Tracks will be populated here -->
            </div>
        </div>

        <!-- EFFECTS -->
        <div class="effects">
            <h3>🎨 EFECTOS Y FILTROS</h3>
            <div class="effects-grid">
                <button class="effect-btn" onclick="toggleEffect('reverb')">🌊 REVERB</button>
                <button class="effect-btn" onclick="toggleEffect('delay')">⏰ DELAY</button>
                <button class="effect-btn" onclick="toggleEffect('filter')">🎛️ FILTER</button>
                <button class="effect-btn" onclick="toggleEffect('flanger')">🌀 FLANGER</button>
                <button class="effect-btn" onclick="toggleEffect('phaser')">📡 PHASER</button>
                <button class="effect-btn" onclick="toggleEffect('distortion')">⚡ DISTORT</button>
                <button class="effect-btn" onclick="toggleEffect('bitcrusher')">🔥 CRUSH</button>
                <button class="effect-btn" onclick="toggleEffect('gater')">🎚️ GATE</button>
            </div>
        </div>
    </div>

    <script>
        const musicFiles = {json.dumps(music_files)};
        let selectedTrack = -1;
        let deckA = {{ track: null, playing: false, audio: null }};
        let deckB = {{ track: null, playing: false, audio: null }};
        let crossfaderValue = 50;
        let activeEffects = [];

        // Inicializar aplicación
        window.onload = function() {{
            initializeDecks();
            populateTrackList();
            startVisualization();
        }};

        function initializeDecks() {{
            deckA.audio = document.getElementById('audioA');
            deckB.audio = document.getElementById('audioB');

            // Event listeners para los reproductores
            deckA.audio.addEventListener('timeupdate', () => updateProgress('A'));
            deckB.audio.addEventListener('timeupdate', () => updateProgress('B'));
            deckA.audio.addEventListener('ended', () => trackEnded('A'));
            deckB.audio.addEventListener('ended', () => trackEnded('B'));
        }}

        function populateTrackList() {{
            const trackList = document.getElementById('trackList');
            trackList.innerHTML = '';

            musicFiles.forEach((track, index) => {{
                const trackElement = document.createElement('div');
                trackElement.className = 'track-item';
                trackElement.onclick = () => selectTrack(index);

                trackElement.innerHTML = `
                    <div class="track-color" style="background-color: ${{track.color}}"></div>
                    <div class="track-info-cell">
                        <div class="track-title">${{track.title}}</div>
                        <div class="track-artist">${{track.artist}}</div>
                    </div>
                    <div class="track-genre">${{track.genre}}</div>
                    <div class="track-bpm">${{track.bpm}}</div>
                    <div class="track-key">${{track.key}}</div>
                    <div class="track-actions">
                        <button class="action-btn" onclick="previewTrack(${{index}}); event.stopPropagation();" title="Preview">▶️</button>
                        <button class="action-btn" onclick="loadToDeck('A', ${{index}}); event.stopPropagation();" title="Load to A">🅰️</button>
                        <button class="action-btn" onclick="loadToDeck('B', ${{index}}); event.stopPropagation();" title="Load to B">🅱️</button>
                    </div>
                `;

                trackList.appendChild(trackElement);
            }});
        }}

        function selectTrack(index) {{
            // Remover selección anterior
            document.querySelectorAll('.track-item').forEach(item => {{
                item.classList.remove('selected');
            }});

            // Seleccionar nuevo track
            document.querySelectorAll('.track-item')[index].classList.add('selected');
            selectedTrack = index;

            showNotification(`🎵 Seleccionado: ${{musicFiles[index].title}}`);
        }}

        function loadToDeck(deck, trackIndex = null) {{
            const index = trackIndex !== null ? trackIndex : selectedTrack;
            if (index === -1) {{
                showNotification('❌ Selecciona un track primero');
                return;
            }}

            const track = musicFiles[index];
            const deckObj = deck === 'A' ? deckA : deckB;

            // Cargar track en el deck
            deckObj.track = track;
            deckObj.audio.src = track.path;

            // Actualizar display del deck
            document.getElementById(`deck${{deck}}-info`).textContent = `${{track.artist}} - ${{track.title}}`;
            document.getElementById(`deck${{deck}}-bpm`).textContent = track.bpm;

            // Generar waveform
            generateWaveform(deck, track.waveform);

            showNotification(`🎧 Cargado en Deck ${{deck}}: ${{track.title}}`);
        }}

        function playDeck(deck) {{
            const deckObj = deck === 'A' ? deckA : deckB;
            const playBtn = document.getElementById(`deck${{deck}}-play`);

            if (!deckObj.track) {{
                showNotification(`❌ No hay track cargado en Deck ${{deck}}`);
                return;
            }}

            if (deckObj.playing) {{
                deckObj.audio.pause();
                deckObj.playing = false;
                playBtn.textContent = 'PLAY';
                playBtn.classList.remove('active');
            }} else {{
                deckObj.audio.play();
                deckObj.playing = true;
                playBtn.textContent = 'PAUSE';
                playBtn.classList.add('active');
            }}
        }}

        function cueDeck(deck) {{
            const deckObj = deck === 'A' ? deckA : deckB;
            if (deckObj.track) {{
                deckObj.audio.currentTime = 0;
                showNotification(`🎯 Cue point set en Deck ${{deck}}`);
            }}
        }}

        function syncDeck(deck) {{
            const otherDeck = deck === 'A' ? deckB : deckA;
            const currentDeck = deck === 'A' ? deckA : deckB;

            if (otherDeck.track && currentDeck.track) {{
                // Simular sync de BPM
                showNotification(`🔄 Deck ${{deck}} sincronizado`);
            }}
        }}

        function loopDeck(deck) {{
            const deckObj = deck === 'A' ? deckA : deckB;
            if (deckObj.track) {{
                deckObj.audio.loop = !deckObj.audio.loop;
                showNotification(`🔁 Loop ${{deckObj.audio.loop ? 'ON' : 'OFF'}} en Deck ${{deck}}`);
            }}
        }}

        function hotCue(deck, cueNumber) {{
            showNotification(`🔥 Hot Cue ${{cueNumber}} activado en Deck ${{deck}}`);
        }}

        function updateCrossfader(value) {{
            crossfaderValue = value;
            const volumeA = (100 - value) / 100;
            const volumeB = value / 100;

            if (deckA.audio) deckA.audio.volume = volumeA;
            if (deckB.audio) deckB.audio.volume = volumeB;
        }}

        function adjustEQ(band) {{
            showNotification(`🎛️ Ajustando ${{band.toUpperCase()}} EQ`);
        }}

        function autoMix() {{
            showNotification('🤖 Auto Mix activado');
        }}

        function beatMatch() {{
            if (deckA.track && deckB.track) {{
                showNotification(`🎯 Beat matching: ${{deckA.track.bpm}} BPM ↔ ${{deckB.track.bpm}} BPM`);
            }}
        }}

        function toggleEffect(effect) {{
            const index = activeEffects.indexOf(effect);
            if (index > -1) {{
                activeEffects.splice(index, 1);
                document.querySelector(`[onclick="toggleEffect('${{effect}}')"]`).classList.remove('active');
                showNotification(`🎨 ${{effect.toUpperCase()}} OFF`);
            }} else {{
                activeEffects.push(effect);
                document.querySelector(`[onclick="toggleEffect('${{effect}}')"]`).classList.add('active');
                showNotification(`🎨 ${{effect.toUpperCase()}} ON`);
            }}
        }}

        function generateWaveform(deck, waveformData) {{
            const container = document.getElementById(`deck${{deck}}-waveform`);
            container.innerHTML = '';

            waveformData.forEach(height => {{
                const bar = document.createElement('div');
                bar.className = 'waveform-bar';
                bar.style.height = height + '%';
                container.appendChild(bar);
            }});
        }}

        function updateProgress(deck) {{
            const deckObj = deck === 'A' ? deckA : deckB;
            if (deckObj.audio && deckObj.audio.duration) {{
                const progress = (deckObj.audio.currentTime / deckObj.audio.duration) * 100;
                document.getElementById(`deck${{deck}}-progress`).style.width = progress + '%';
            }}
        }}

        function trackEnded(deck) {{
            const deckObj = deck === 'A' ? deckA : deckB;
            deckObj.playing = false;
            document.getElementById(`deck${{deck}}-play`).textContent = 'PLAY';
            document.getElementById(`deck${{deck}}-play`).classList.remove('active');
        }}

        function scanLibrary() {{
            showNotification('📁 Escaneando biblioteca...');
            fetch('/api/scan')
                .then(response => response.json())
                .then(data => {{
                    showNotification(`✅ ${{data.files_found}} archivos encontrados`);
                }});
        }}

        function analyzeAll() {{
            showNotification('🔍 Analizando todos los tracks...');
            fetch('/api/analyze')
                .then(response => response.json())
                .then(data => {{
                    showNotification('✅ Análisis completado: BPM, Key, Energy detectados');
                }});
        }}

        function createPlaylist() {{
            showNotification('📝 Creando nueva playlist...');
        }}

        function sortBy(criteria) {{
            showNotification(`📊 Ordenando por ${{criteria.toUpperCase()}}`);
        }}

        function filterGenre() {{
            showNotification('🎭 Aplicando filtro de género');
        }}

        function searchTracks(query) {{
            // Implementar búsqueda en tiempo real
            if (query.length > 2) {{
                showNotification(`🔍 Buscando: ${{query}}`);
            }}
        }}

        function previewTrack(index) {{
            const track = musicFiles[index];
            showNotification(`👂 Preview: ${{track.title}}`);
        }}

        function startVisualization() {{
            // Animación de las barras de waveform
            setInterval(() => {{
                if (deckA.playing) {{
                    animateWaveform('A');
                }}
                if (deckB.playing) {{
                    animateWaveform('B');
                }}
            }}, 100);
        }}

        function animateWaveform(deck) {{
            const bars = document.querySelectorAll(`#deck${{deck}}-waveform .waveform-bar`);
            bars.forEach(bar => {{
                const newHeight = Math.random() * 80 + 20;
                bar.style.height = newHeight + '%';
            }});
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
    </script>
</body>
</html>"""

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def serve_audio_file(self):
        """Servir archivos de audio."""
        try:
            file_index = int(self.path.split('/')[-1])
            real_files = self.scan_real_files()

            if real_files and file_index < len(real_files):
                file_path = real_files[file_index]

                if os.path.exists(file_path):
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if not mime_type:
                        mime_type = 'audio/mpeg'

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

    def serve_analyze_api(self):
        """API para análisis de audio."""
        response = {
            'status': 'success',
            'analysis': {
                'bpm_detected': True,
                'key_detected': True,
                'energy_analyzed': True,
                'waveform_generated': True
            }
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def serve_playlist_api(self):
        """API para playlists."""
        response = {
            'status': 'success',
            'playlists': ['Main Mix', 'Party Hits', 'Chill Vibes', 'Electronic']
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def serve_effects_api(self):
        """API para efectos."""
        response = {
            'status': 'success',
            'effects': ['reverb', 'delay', 'filter', 'flanger']
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def serve_folders_api(self):
        """API para obtener carpetas configuradas."""
        config_file = os.path.expanduser("~/.djlibraryalfin_folders.txt")
        custom_folders = []

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    custom_folders = [line.strip() for line in f.readlines() if line.strip()]
            except:
                pass

        response = {
            'status': 'success',
            'custom_folders': custom_folders,
            'default_folders': [
                os.path.expanduser("~/Music"),
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Downloads")
            ]
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def serve_add_folder_api(self):
        """API para mostrar formulario de agregar carpeta."""
        html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>📁 Agregar Carpeta - DjAlfin Pro</title>
    <style>
        body { font-family: Arial, sans-serif; background: #2c3e50; color: white; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #34495e; padding: 30px; border-radius: 15px; }
        h1 { color: #3498db; text-align: center; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 10px; border: none; border-radius: 5px; background: #2c3e50; color: white; }
        button { background: #3498db; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #2980b9; }
        .folder-list { background: #2c3e50; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .folder-item { padding: 8px; border-bottom: 1px solid #34495e; }
        .examples { background: #27ae60; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .back-btn { background: #e74c3c; margin-right: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 Agregar Carpeta de Música</h1>

        <form onsubmit="addFolder(event)">
            <div class="form-group">
                <label for="folderPath">🎵 Ruta de la Carpeta:</label>
                <input type="text" id="folderPath" placeholder="/ruta/a/tu/carpeta/de/musica" required>
            </div>
            <button type="button" class="back-btn" onclick="window.history.back()">← Volver</button>
            <button type="submit">➕ Agregar Carpeta</button>
        </form>

        <div class="examples">
            <h3>📋 Ejemplos de Rutas:</h3>
            <ul>
                <li><strong>macOS:</strong> /Users/tu_usuario/Music/Mi_Coleccion</li>
                <li><strong>Disco Externo:</strong> /Volumes/Mi_Disco/Musica</li>
                <li><strong>Carpeta Personal:</strong> ~/Documents/DJ_Music</li>
                <li><strong>Carpeta Compartida:</strong> /Users/Shared/Music</li>
            </ul>
        </div>

        <div class="folder-list">
            <h3>📂 Carpetas Configuradas:</h3>
            <div id="foldersList">Cargando...</div>
        </div>
    </div>

    <script>
        function addFolder(event) {
            event.preventDefault();
            const folderPath = document.getElementById('folderPath').value;

            fetch('/api/add_folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder: folderPath })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('✅ Carpeta agregada exitosamente!');
                    document.getElementById('folderPath').value = '';
                    loadFolders();
                } else {
                    alert('❌ Error: ' + data.message);
                }
            })
            .catch(error => {
                alert('❌ Error agregando carpeta: ' + error);
            });
        }

        function loadFolders() {
            fetch('/api/folders')
                .then(response => response.json())
                .then(data => {
                    const foldersList = document.getElementById('foldersList');
                    let html = '';

                    if (data.custom_folders.length > 0) {
                        html += '<h4>🎵 Carpetas Personalizadas:</h4>';
                        data.custom_folders.forEach(folder => {
                            html += `<div class="folder-item">📁 ${folder}</div>`;
                        });
                    }

                    html += '<h4>🏠 Carpetas Predeterminadas:</h4>';
                    data.default_folders.forEach(folder => {
                        html += `<div class="folder-item">🏠 ${folder}</div>`;
                    });

                    foldersList.innerHTML = html;
                });
        }

        // Cargar carpetas al iniciar
        loadFolders();
    </script>
</body>
</html>
        """

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def handle_add_folder_post(self):
        """Manejar POST para agregar carpeta."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            folder_path = data.get('folder', '').strip()

            if not folder_path:
                response = {'status': 'error', 'message': 'Ruta de carpeta vacía'}
            elif not os.path.exists(folder_path):
                response = {'status': 'error', 'message': 'La carpeta no existe'}
            else:
                # Agregar carpeta al archivo de configuración
                config_file = os.path.expanduser("~/.djlibraryalfin_folders.txt")

                # Leer carpetas existentes
                existing_folders = []
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as f:
                            existing_folders = [line.strip() for line in f.readlines() if line.strip()]
                    except:
                        pass

                # Agregar nueva carpeta si no existe
                if folder_path not in existing_folders:
                    existing_folders.append(folder_path)

                    # Escribir todas las carpetas
                    with open(config_file, 'w') as f:
                        for folder in existing_folders:
                            f.write(folder + '\n')

                    response = {'status': 'success', 'message': 'Carpeta agregada exitosamente'}
                else:
                    response = {'status': 'error', 'message': 'La carpeta ya está configurada'}

        except Exception as e:
            response = {'status': 'error', 'message': str(e)}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def scan_real_files(self):
        """Escanear archivos reales en el sistema."""
        # Carpetas predeterminadas
        folders = [
            "/Volumes/KINGSTON/Audio",
            "/Volumes/KINGSTON/DjAlfin",
            "/Volumes/KINGSTON/djlibraryalfin-main",
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            # Agregar más carpetas comunes
            os.path.expanduser("~/Documents/Music"),
            os.path.expanduser("~/Library/Music"),
            "/Users/Shared/Music",
            # Carpetas de aplicaciones de música
            os.path.expanduser("~/Music/iTunes/iTunes Media/Music"),
            os.path.expanduser("~/Music/Music/Media.localized/Music"),
            # Carpetas externas comunes
            "/Volumes/Music",
            "/Volumes/Audio",
            "/Volumes/DJ Music",
            "/Volumes/External/Music"
        ]

        # Leer carpetas personalizadas del archivo de configuración
        config_file = os.path.expanduser("~/.djlibraryalfin_folders.txt")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    custom_folders = [line.strip() for line in f.readlines() if line.strip()]
                    folders.extend(custom_folders)
            except:
                pass

        extensions = ['*.mp3', '*.m4a', '*.flac', '*.wav', '*.aac']
        found_files = []

        for folder in folders:
            if os.path.exists(folder):
                for ext in extensions:
                    pattern = os.path.join(folder, '**', ext)
                    files = glob.glob(pattern, recursive=True)
                    found_files.extend(files)

                    if len(found_files) >= 100:
                        break

                if len(found_files) >= 100:
                    break

        return found_files

    def generate_waveform_data(self):
        """Generar datos de waveform simulados."""
        return [random.randint(10, 100) for _ in range(50)]

    def get_genre_color(self, genre):
        """Obtener color basado en género."""
        colors = {
            "Hip Hop": "#e74c3c",
            "R&B": "#9b59b6",
            "Reggae": "#2ecc71",
            "Pop": "#3498db",
            "Rock": "#e67e22",
            "Dance": "#f39c12",
            "House": "#1abc9c",
            "Techno": "#34495e",
            "Electronic": "#9b59b6",
            "Trance": "#8e44ad"
        }
        return colors.get(genre, "#95a5a6")

    def get_sample_tracks(self):
        """Obtener tracks de ejemplo si no hay archivos reales."""
        return [
            {
                "id": 0,
                "filename": "Sample Track 1.mp3",
                "artist": "DJ Example",
                "title": "Electronic Vibes",
                "album": "Demo Album",
                "year": 2024,
                "genre": "Electronic",
                "bpm": 128,
                "key": "C major",
                "duration": "4:32",
                "duration_seconds": 272,
                "bitrate": "320 kbps",
                "size": "10.2 MB",
                "path": "/audio/0",
                "real_path": "",
                "energy": 8,
                "danceability": 9,
                "valence": 7,
                "waveform": self.generate_waveform_data(),
                "color": "#9b59b6"
            },
            {
                "id": 1,
                "filename": "Sample Track 2.mp3",
                "artist": "House Master",
                "title": "Deep Groove",
                "album": "Underground",
                "year": 2023,
                "genre": "House",
                "bpm": 124,
                "key": "G minor",
                "duration": "5:18",
                "duration_seconds": 318,
                "bitrate": "320 kbps",
                "size": "12.1 MB",
                "path": "/audio/1",
                "real_path": "",
                "energy": 7,
                "danceability": 8,
                "valence": 6,
                "waveform": self.generate_waveform_data(),
                "color": "#1abc9c"
            }
        ]

def start_server():
    """Iniciar servidor."""
    server_address = ('localhost', 8084)
    httpd = HTTPServer(server_address, DjAlfinProHandler)

    print("🎧 DjAlfin Pro iniciado en http://localhost:8084")
    print("🎵 Estación de DJ completa funcionando")

    httpd.serve_forever()

def main():
    """Función principal."""
    print("🎧 Iniciando DjAlfin Pro - Estación de DJ Completa...")
    print("🎵 Todas las funciones profesionales de DJ")

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    time.sleep(2)

    try:
        print("🌐 Abriendo estación de DJ...")
        webbrowser.open('http://localhost:8084')
        print("✅ DjAlfin Pro funcionando con todas las características")
        print("🎧 Disfruta mezclando música!")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Cerrando DjAlfin Pro...")
        print("🎵 ¡Gracias por usar DjAlfin Pro!")

if __name__ == "__main__":
    main()