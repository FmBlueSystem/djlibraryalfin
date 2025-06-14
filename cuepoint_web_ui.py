#!/usr/bin/env python3
"""
🎯 DjAlfin - Interfaz Web Moderna para Cue Points
Prototipo web con diseño profesional estilo DJ software
"""

import os
import json
import time
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
from urllib.parse import parse_qs, urlparse

class CuePointWebHandler(BaseHTTPRequestHandler):
    """Handler para la interfaz web de cue points."""
    
    def do_GET(self):
        """Manejar peticiones GET."""
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Manejar peticiones POST."""
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404)
    
    def serve_main_page(self):
        """Servir página principal."""
        html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 DjAlfin Pro - Cue Points Studio</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #21262d 100%);
            color: #f0f6fc;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .header {
            background: linear-gradient(90deg, #0d1117, #21262d);
            padding: 20px;
            border-bottom: 2px solid #30363d;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }
        
        .header h1 {
            color: #58a6ff;
            font-size: 2.5em;
            text-shadow: 0 0 20px rgba(88, 166, 255, 0.5);
            margin-bottom: 5px;
        }
        
        .header p {
            color: #8b949e;
            font-size: 1.1em;
        }
        
        .main-container {
            display: grid;
            grid-template-columns: 300px 1fr 350px;
            grid-template-rows: 1fr auto;
            gap: 20px;
            padding: 20px;
            min-height: calc(100vh - 120px);
        }
        
        .control-panel {
            background: linear-gradient(145deg, #21262d, #30363d);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #30363d;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .panel-title {
            color: #58a6ff;
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 20px;
            text-align: center;
            text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
        }
        
        .waveform-container {
            background: linear-gradient(145deg, #0d1117, #161b22);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #30363d;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .info-panel {
            background: linear-gradient(145deg, #21262d, #30363d);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #30363d;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .hotcue-panel {
            grid-column: 1 / -1;
            background: linear-gradient(145deg, #0d1117, #21262d);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #30363d;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .playback-controls {
            background: #161b22;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }
        
        .position-display {
            background: #0d1117;
            color: #f85149;
            font-family: 'Courier New', monospace;
            font-size: 1.8em;
            font-weight: bold;
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 2px solid #30363d;
            text-shadow: 0 0 10px rgba(248, 81, 73, 0.5);
        }
        
        .position-slider {
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: #30363d;
            outline: none;
            margin-bottom: 15px;
            cursor: pointer;
        }
        
        .position-slider::-webkit-slider-thumb {
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #58a6ff;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(88, 166, 255, 0.5);
        }
        
        .control-buttons {
            display: flex;
            gap: 10px;
            justify-content: center;
        }
        
        .btn {
            background: linear-gradient(145deg, #238636, #2ea043);
            color: white;
            border: none;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(35, 134, 54, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(35, 134, 54, 0.4);
        }
        
        .btn.stop { background: linear-gradient(145deg, #da3633, #f85149); }
        .btn.nav { background: linear-gradient(145deg, #6f42c1, #8957e5); }
        
        .waveform {
            height: 200px;
            background: #000000;
            border-radius: 10px;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
            border: 2px solid #30363d;
            cursor: crosshair;
        }
        
        .waveform-bars {
            display: flex;
            height: 100%;
            align-items: end;
            padding: 5px;
        }
        
        .waveform-bar {
            flex: 1;
            margin: 0 1px;
            border-radius: 1px;
            transition: height 0.1s ease;
            cursor: pointer;
        }
        
        .position-line {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #f0f6fc;
            box-shadow: 0 0 10px rgba(240, 246, 252, 0.8);
            z-index: 10;
            transition: left 0.1s ease;
        }
        
        .cue-marker {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 3px;
            z-index: 5;
            cursor: pointer;
        }
        
        .cue-label {
            position: absolute;
            top: 5px;
            font-size: 0.8em;
            font-weight: bold;
            background: rgba(0, 0, 0, 0.7);
            padding: 2px 6px;
            border-radius: 4px;
            white-space: nowrap;
            transform: translateX(-50%);
        }
        
        .timeline {
            height: 40px;
            background: #161b22;
            border-radius: 8px;
            position: relative;
            border: 1px solid #30363d;
        }
        
        .time-marker {
            position: absolute;
            bottom: 0;
            width: 1px;
            height: 15px;
            background: #8b949e;
        }
        
        .time-label {
            position: absolute;
            bottom: 20px;
            font-size: 0.8em;
            color: #8b949e;
            transform: translateX(-50%);
        }
        
        .cue-creator {
            background: #161b22;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #f0f6fc;
        }
        
        .form-input {
            width: 100%;
            padding: 8px 12px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #f0f6fc;
            font-size: 1em;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #58a6ff;
            box-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
        }
        
        .color-selector {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 5px;
        }
        
        .color-option {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            border: 3px solid transparent;
            transition: all 0.2s ease;
        }
        
        .color-option:hover {
            transform: scale(1.1);
            border-color: #f0f6fc;
        }
        
        .color-option.selected {
            border-color: #58a6ff;
            box-shadow: 0 0 15px rgba(88, 166, 255, 0.5);
        }
        
        .energy-slider {
            width: 100%;
            margin-top: 10px;
        }
        
        .cue-list {
            max-height: 300px;
            overflow-y: auto;
            background: #0d1117;
            border-radius: 8px;
            border: 1px solid #30363d;
        }
        
        .cue-item {
            display: flex;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #21262d;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .cue-item:hover {
            background: #161b22;
        }
        
        .cue-item.selected {
            background: #1f2937;
            border-left: 4px solid #58a6ff;
        }
        
        .cue-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 12px;
            border: 2px solid #30363d;
        }
        
        .cue-info {
            flex: 1;
        }
        
        .cue-name {
            font-weight: bold;
            margin-bottom: 2px;
        }
        
        .cue-details {
            font-size: 0.9em;
            color: #8b949e;
        }
        
        .cue-actions {
            display: flex;
            gap: 5px;
        }
        
        .action-btn {
            background: none;
            border: none;
            color: #8b949e;
            cursor: pointer;
            padding: 5px;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        
        .action-btn:hover {
            background: #30363d;
            color: #f0f6fc;
        }
        
        .hotcue-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .hotcue-btn {
            height: 80px;
            background: linear-gradient(145deg, #30363d, #21262d);
            border: 2px solid #30363d;
            border-radius: 12px;
            color: #8b949e;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .hotcue-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        
        .hotcue-btn.assigned {
            border-color: currentColor;
            box-shadow: 0 0 20px currentColor;
        }
        
        .hotcue-number {
            font-size: 1.5em;
            margin-bottom: 5px;
        }
        
        .hotcue-name {
            font-size: 0.8em;
            text-align: center;
        }
        
        .analysis-controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }
        
        .analysis-btn {
            background: linear-gradient(145deg, #0969da, #1f6feb);
            color: white;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .analysis-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(9, 105, 218, 0.4);
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(145deg, #238636, #2ea043);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @media (max-width: 1200px) {
            .main-container {
                grid-template-columns: 1fr;
                grid-template-rows: auto;
            }
            
            .hotcue-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 DjAlfin Pro</h1>
        <p>Professional Cue Points Studio - Web Interface</p>
    </div>
    
    <div class="main-container">
        <!-- Control Panel -->
        <div class="control-panel">
            <div class="panel-title">🎛️ CONTROL PANEL</div>
            
            <!-- Playback Controls -->
            <div class="playback-controls">
                <div class="position-display" id="positionDisplay">0:00</div>
                <input type="range" class="position-slider" id="positionSlider" 
                       min="0" max="300" value="0" step="0.1">
                <div class="control-buttons">
                    <button class="btn" id="playBtn" onclick="togglePlay()">▶️</button>
                    <button class="btn stop" onclick="stopPlayback()">⏹️</button>
                    <button class="btn nav" onclick="previousCue()">⏮️</button>
                    <button class="btn nav" onclick="nextCue()">⏭️</button>
                </div>
            </div>
            
            <!-- Cue Creator -->
            <div class="cue-creator">
                <div class="form-group">
                    <label class="form-label">Name:</label>
                    <input type="text" class="form-input" id="cueName" placeholder="Enter cue name">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Color:</label>
                    <div class="color-selector" id="colorSelector">
                        <div class="color-option selected" data-color="#FF0000" style="background: #FF0000"></div>
                        <div class="color-option" data-color="#FF6600" style="background: #FF6600"></div>
                        <div class="color-option" data-color="#FFFF00" style="background: #FFFF00"></div>
                        <div class="color-option" data-color="#00FF00" style="background: #00FF00"></div>
                        <div class="color-option" data-color="#00FFFF" style="background: #00FFFF"></div>
                        <div class="color-option" data-color="#0066FF" style="background: #0066FF"></div>
                        <div class="color-option" data-color="#9900FF" style="background: #9900FF"></div>
                        <div class="color-option" data-color="#FF00CC" style="background: #FF00CC"></div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Energy: <span id="energyValue">5</span>/10</label>
                    <input type="range" class="energy-slider" id="energySlider" 
                           min="1" max="10" value="5" oninput="updateEnergyDisplay()">
                </div>
                
                <button class="btn" onclick="addCuePoint()" style="width: 100%; margin-top: 10px;">
                    ➕ Add Cue Point
                </button>
            </div>
            
            <!-- Analysis Controls -->
            <div class="analysis-controls">
                <button class="analysis-btn" onclick="autoDetectCues()">🔍 Auto Detect</button>
                <button class="analysis-btn" onclick="analyzeEnergy()">🎵 Energy</button>
                <button class="analysis-btn" onclick="findBeatGrid()">🥁 Beat Grid</button>
                <button class="analysis-btn" onclick="detectKey()">🎹 Key</button>
            </div>
        </div>
        
        <!-- Waveform Container -->
        <div class="waveform-container">
            <div class="panel-title">🌊 WAVEFORM STUDIO</div>
            
            <div class="waveform" id="waveform" onclick="onWaveformClick(event)">
                <div class="waveform-bars" id="waveformBars"></div>
                <div class="position-line" id="positionLine"></div>
            </div>
            
            <div class="timeline" id="timeline"></div>
            
            <div style="text-align: center; margin-top: 15px;">
                <label style="margin-right: 10px;">🔍 Zoom:</label>
                <input type="range" id="zoomSlider" min="0.5" max="5" value="1" step="0.1" 
                       style="width: 200px;" oninput="updateZoom()">
                <span id="zoomValue">1.0x</span>
            </div>
        </div>
        
        <!-- Info Panel -->
        <div class="info-panel">
            <div class="panel-title">📋 CUE POINT LIST</div>
            
            <div class="cue-list" id="cueList">
                <!-- Cue points will be populated here -->
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button class="btn" onclick="saveCues()" style="flex: 1;">💾 Save</button>
                <button class="btn" onclick="loadCues()" style="flex: 1;">📁 Load</button>
                <button class="btn stop" onclick="deleteSelected()" style="flex: 1;">🗑️ Delete</button>
            </div>
        </div>
        
        <!-- Hot Cue Panel -->
        <div class="hotcue-panel">
            <div class="panel-title">🔥 HOT CUES</div>
            
            <div class="hotcue-grid" id="hotcueGrid">
                <!-- Hot cue buttons will be generated here -->
            </div>
        </div>
    </div>
    
    <script>
        // Global variables
        let cuePoints = [];
        let currentPosition = 0;
        let trackDuration = 300;
        let isPlaying = false;
        let selectedColor = '#FF0000';
        let selectedCueIndex = -1;
        let waveformData = [];
        let zoom = 1.0;
        
        // Initialize application
        window.onload = function() {
            generateWaveformData();
            createHotCueButtons();
            loadDemoData();
            updateAllDisplays();
            startAnimationLoop();
        };
        
        // Generate realistic waveform data
        function generateWaveformData() {
            waveformData = [];
            for (let i = 0; i < 1000; i++) {
                const pos = i / 1000;
                let intensity;
                
                if (pos < 0.1) {
                    intensity = 0.3 + 0.2 * Math.sin(pos * 20);
                } else if (pos < 0.25) {
                    intensity = 0.3 + pos * 2;
                } else if (pos < 0.5) {
                    intensity = 0.8 + 0.2 * Math.sin(pos * 50);
                } else if (pos < 0.75) {
                    intensity = 0.4 + 0.3 * Math.sin(pos * 30);
                } else {
                    intensity = 0.8 - (pos - 0.75) * 2;
                }
                
                intensity += (Math.random() - 0.5) * 0.2;
                intensity = Math.max(0, Math.min(1, intensity));
                waveformData.push(intensity);
            }
        }
        
        // Create hot cue buttons
        function createHotCueButtons() {
            const grid = document.getElementById('hotcueGrid');
            grid.innerHTML = '';
            
            for (let i = 1; i <= 8; i++) {
                const btn = document.createElement('div');
                btn.className = 'hotcue-btn';
                btn.onclick = () => triggerHotCue(i);
                btn.innerHTML = `
                    <div class="hotcue-number">${i}</div>
                    <div class="hotcue-name">-</div>
                `;
                btn.id = `hotcue${i}`;
                grid.appendChild(btn);
            }
        }
        
        // Load demo data
        function loadDemoData() {
            cuePoints = [
                { position: 15.5, name: "Intro Drop", color: "#FF0000", energy: 7, hotcue: 1, created: Date.now() },
                { position: 45.2, name: "Verse Start", color: "#FF6600", energy: 5, hotcue: 2, created: Date.now() },
                { position: 75.8, name: "Pre-Chorus", color: "#FFFF00", energy: 6, hotcue: 3, created: Date.now() },
                { position: 105.3, name: "Main Drop", color: "#00FF00", energy: 9, hotcue: 4, created: Date.now() },
                { position: 135.7, name: "Breakdown", color: "#00FFFF", energy: 3, hotcue: 5, created: Date.now() },
                { position: 165.1, name: "Build Up", color: "#0066FF", energy: 7, hotcue: 6, created: Date.now() },
                { position: 195.4, name: "Final Drop", color: "#9900FF", energy: 10, hotcue: 7, created: Date.now() },
                { position: 225.8, name: "Outro", color: "#FF00CC", energy: 4, hotcue: 8, created: Date.now() }
            ];
        }

        // Update all displays
        function updateAllDisplays() {
            updateWaveform();
            updateTimeline();
            updateCueList();
            updateHotCueButtons();
            updatePositionDisplay();
        }

        // Update waveform display
        function updateWaveform() {
            const container = document.getElementById('waveformBars');
            const waveform = document.getElementById('waveform');
            const positionLine = document.getElementById('positionLine');

            container.innerHTML = '';

            // Clear existing cue markers
            const existingMarkers = waveform.querySelectorAll('.cue-marker');
            existingMarkers.forEach(marker => marker.remove());

            const width = waveform.clientWidth;
            const barCount = Math.min(width / 2, waveformData.length);

            for (let i = 0; i < barCount; i++) {
                const dataIndex = Math.floor((i / barCount) * waveformData.length);
                const intensity = waveformData[dataIndex];

                const bar = document.createElement('div');
                bar.className = 'waveform-bar';
                bar.style.height = (intensity * 90) + '%';

                if (intensity > 0.7) {
                    bar.style.background = '#ff4444';
                } else if (intensity > 0.4) {
                    bar.style.background = '#ffaa00';
                } else {
                    bar.style.background = '#4488ff';
                }

                container.appendChild(bar);
            }

            // Update position line
            const positionPercent = (currentPosition / trackDuration) * 100;
            positionLine.style.left = positionPercent + '%';

            // Add cue markers
            cuePoints.forEach(cue => {
                const cuePercent = (cue.position / trackDuration) * 100;

                const marker = document.createElement('div');
                marker.className = 'cue-marker';
                marker.style.left = cuePercent + '%';
                marker.style.background = cue.color;
                marker.onclick = () => jumpToCue(cue);

                const label = document.createElement('div');
                label.className = 'cue-label';
                label.textContent = cue.name.substring(0, 8);
                label.style.color = cue.color;
                label.style.left = '50%';

                marker.appendChild(label);
                waveform.appendChild(marker);
            });
        }

        // Update timeline
        function updateTimeline() {
            const timeline = document.getElementById('timeline');
            timeline.innerHTML = '';

            const width = timeline.clientWidth;
            const timeStep = 30; // 30 seconds
            const markerCount = Math.floor(trackDuration / timeStep) + 1;

            for (let i = 0; i < markerCount; i++) {
                const time = i * timeStep;
                const percent = (time / trackDuration) * 100;

                const marker = document.createElement('div');
                marker.className = 'time-marker';
                marker.style.left = percent + '%';

                const label = document.createElement('div');
                label.className = 'time-label';
                label.textContent = formatTime(time);
                label.style.left = percent + '%';

                timeline.appendChild(marker);
                timeline.appendChild(label);
            }
        }

        // Update cue list
        function updateCueList() {
            const list = document.getElementById('cueList');
            list.innerHTML = '';

            const sortedCues = [...cuePoints].sort((a, b) => a.position - b.position);

            sortedCues.forEach((cue, index) => {
                const item = document.createElement('div');
                item.className = 'cue-item';
                if (index === selectedCueIndex) {
                    item.classList.add('selected');
                }

                item.onclick = () => selectCue(index);
                item.ondblclick = () => jumpToCue(cue);

                item.innerHTML = `
                    <div class="cue-color" style="background: ${cue.color}"></div>
                    <div class="cue-info">
                        <div class="cue-name">${cue.name}</div>
                        <div class="cue-details">
                            ${formatTime(cue.position)} • Energy: ${cue.energy}/10 • Hot: ${cue.hotcue || '-'}
                        </div>
                    </div>
                    <div class="cue-actions">
                        <button class="action-btn" onclick="jumpToCue(cuePoints[${cuePoints.indexOf(cue)}]); event.stopPropagation();">▶️</button>
                        <button class="action-btn" onclick="deleteCue(${cuePoints.indexOf(cue)}); event.stopPropagation();">🗑️</button>
                    </div>
                `;

                list.appendChild(item);
            });
        }

        // Update hot cue buttons
        function updateHotCueButtons() {
            for (let i = 1; i <= 8; i++) {
                const btn = document.getElementById(`hotcue${i}`);
                const cue = cuePoints.find(c => c.hotcue === i);

                if (cue) {
                    btn.className = 'hotcue-btn assigned';
                    btn.style.color = cue.color;
                    btn.style.borderColor = cue.color;
                    btn.innerHTML = `
                        <div class="hotcue-number">${i}</div>
                        <div class="hotcue-name">${cue.name.substring(0, 8)}</div>
                    `;
                } else {
                    btn.className = 'hotcue-btn';
                    btn.style.color = '#8b949e';
                    btn.style.borderColor = '#30363d';
                    btn.innerHTML = `
                        <div class="hotcue-number">${i}</div>
                        <div class="hotcue-name">-</div>
                    `;
                }
            }
        }

        // Update position display
        function updatePositionDisplay() {
            document.getElementById('positionDisplay').textContent = formatTime(currentPosition);
            document.getElementById('positionSlider').value = currentPosition;
        }

        // Format time as MM:SS
        function formatTime(seconds) {
            const minutes = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }

        // Animation loop
        function startAnimationLoop() {
            setInterval(() => {
                if (isPlaying) {
                    currentPosition += 0.05;
                    if (currentPosition >= trackDuration) {
                        stopPlayback();
                    } else {
                        updatePositionDisplay();
                        updateWaveform();
                    }
                }
            }, 50);
        }

        // Playback controls
        function togglePlay() {
            isPlaying = !isPlaying;
            const btn = document.getElementById('playBtn');
            btn.textContent = isPlaying ? '⏸️' : '▶️';
            btn.style.background = isPlaying ?
                'linear-gradient(145deg, #fd7e14, #fd7e14)' :
                'linear-gradient(145deg, #238636, #2ea043)';
        }

        function stopPlayback() {
            isPlaying = false;
            currentPosition = 0;
            document.getElementById('playBtn').textContent = '▶️';
            document.getElementById('playBtn').style.background = 'linear-gradient(145deg, #238636, #2ea043)';
            updateAllDisplays();
        }

        function previousCue() {
            const sortedCues = [...cuePoints].sort((a, b) => a.position - b.position);
            const prevCue = sortedCues.reverse().find(cue => cue.position < currentPosition - 1);
            if (prevCue) {
                jumpToCue(prevCue);
                showNotification(`⏮️ ${prevCue.name}`);
            }
        }

        function nextCue() {
            const sortedCues = [...cuePoints].sort((a, b) => a.position - b.position);
            const nextCue = sortedCues.find(cue => cue.position > currentPosition + 1);
            if (nextCue) {
                jumpToCue(nextCue);
                showNotification(`⏭️ ${nextCue.name}`);
            }
        }

        // Cue point functions
        function addCuePoint() {
            const name = document.getElementById('cueName').value.trim() || `Cue ${cuePoints.length + 1}`;
            const energy = parseInt(document.getElementById('energySlider').value);

            // Find next available hot cue
            let hotcue = 0;
            for (let i = 1; i <= 8; i++) {
                if (!cuePoints.find(c => c.hotcue === i)) {
                    hotcue = i;
                    break;
                }
            }

            const cuePoint = {
                position: currentPosition,
                name: name,
                color: selectedColor,
                energy: energy,
                hotcue: hotcue,
                created: Date.now()
            };

            cuePoints.push(cuePoint);
            updateAllDisplays();

            document.getElementById('cueName').value = '';
            showNotification(`✅ Added: ${name} @ ${formatTime(currentPosition)}`);
        }

        function deleteCue(index) {
            const cue = cuePoints[index];
            cuePoints.splice(index, 1);
            updateAllDisplays();
            showNotification(`🗑️ Deleted: ${cue.name}`);
        }

        function deleteSelected() {
            if (selectedCueIndex >= 0 && selectedCueIndex < cuePoints.length) {
                deleteCue(selectedCueIndex);
                selectedCueIndex = -1;
            } else {
                showNotification('⚠️ Select a cue point to delete');
            }
        }

        function selectCue(index) {
            selectedCueIndex = index;
            updateCueList();
        }

        function jumpToCue(cue) {
            currentPosition = cue.position;
            updateAllDisplays();
            showNotification(`🎯 ${cue.name}`);
        }

        function triggerHotCue(number) {
            const cue = cuePoints.find(c => c.hotcue === number);
            if (cue) {
                jumpToCue(cue);
                showNotification(`🔥 Hot Cue ${number}: ${cue.name}`);
            } else {
                showNotification(`🔥 Hot Cue ${number}: Not assigned`);
            }
        }

        // Event handlers
        function onWaveformClick(event) {
            const waveform = event.currentTarget;
            const rect = waveform.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const percent = x / rect.width;
            currentPosition = percent * trackDuration;
            updateAllDisplays();
        }

        // Position slider
        document.getElementById('positionSlider').oninput = function() {
            currentPosition = parseFloat(this.value);
            updateAllDisplays();
        };

        // Color selector
        document.querySelectorAll('.color-option').forEach(option => {
            option.onclick = function() {
                document.querySelectorAll('.color-option').forEach(o => o.classList.remove('selected'));
                this.classList.add('selected');
                selectedColor = this.dataset.color;
            };
        });

        // Energy slider
        function updateEnergyDisplay() {
            const value = document.getElementById('energySlider').value;
            document.getElementById('energyValue').textContent = value;
        }

        // Zoom control
        function updateZoom() {
            zoom = parseFloat(document.getElementById('zoomSlider').value);
            document.getElementById('zoomValue').textContent = zoom.toFixed(1) + 'x';
            updateWaveform();
        }

        // Analysis functions
        function autoDetectCues() {
            showNotification('🔍 Analyzing track for cue points...');

            setTimeout(() => {
                const autoCues = [];
                for (let i = 0; i < 5; i++) {
                    const pos = Math.random() * (trackDuration - 40) + 20;
                    const colors = ['#FF0000', '#FF6600', '#FFFF00', '#00FF00', '#00FFFF'];

                    autoCues.push({
                        position: pos,
                        name: `Auto ${i + 1}`,
                        color: colors[i],
                        energy: Math.floor(Math.random() * 5) + 6,
                        hotcue: 0,
                        created: Date.now()
                    });
                }

                cuePoints.push(...autoCues);
                updateAllDisplays();
                showNotification(`✅ Detected ${autoCues.length} cue points automatically`);
            }, 1500);
        }

        function analyzeEnergy() {
            showNotification('🎵 Analyzing energy levels...');
            setTimeout(() => showNotification('✅ Energy analysis complete'), 1200);
        }

        function findBeatGrid() {
            showNotification('🥁 Analyzing beat grid...');
            setTimeout(() => showNotification('✅ Beat grid found: 128 BPM'), 1000);
        }

        function detectKey() {
            const keys = ['C major', 'G major', 'D major', 'A major', 'A minor', 'E minor'];
            const detectedKey = keys[Math.floor(Math.random() * keys.length)];
            showNotification(`🎹 Key detected: ${detectedKey}`);
        }

        // File operations
        function saveCues() {
            const data = {
                version: '2.0',
                trackName: 'Demo Track - Progressive House',
                trackDuration: trackDuration,
                bpm: 128,
                key: 'A minor',
                cuePoints: cuePoints,
                createdAt: Date.now()
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'djalfin_cuepoints.json';
            a.click();
            URL.revokeObjectURL(url);

            showNotification('💾 Cue points saved to file');
        }

        function loadCues() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = function(event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        try {
                            const data = JSON.parse(e.target.result);
                            cuePoints = data.cuePoints || [];
                            trackDuration = data.trackDuration || 300;

                            document.getElementById('positionSlider').max = trackDuration;
                            updateAllDisplays();
                            showNotification(`📁 Loaded ${cuePoints.length} cue points`);
                        } catch (error) {
                            showNotification('❌ Error loading file');
                        }
                    };
                    reader.readAsText(file);
                }
            };
            input.click();
        }

        // Notification system
        function showNotification(message) {
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.textContent = message;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    </script>
</body>
</html>
        """

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def handle_api_request(self):
        """Manejar peticiones API."""
        response = {'status': 'success', 'message': 'API funcionando'}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def handle_api_post(self):
        """Manejar peticiones POST API."""
        response = {'status': 'success', 'message': 'POST recibido'}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

def start_web_server():
    """Iniciar servidor web."""
    server_address = ('localhost', 8085)
    httpd = HTTPServer(server_address, CuePointWebHandler)

    print("🌐 DjAlfin Cue Points Web UI iniciado en http://localhost:8085")
    print("🎯 Interfaz web moderna funcionando")

    httpd.serve_forever()

def main():
    """Función principal."""
    print("🎯 DjAlfin - Interfaz Web de Cue Points")
    print("🌐 Iniciando servidor web...")

    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()

    time.sleep(2)

    try:
        print("🌐 Abriendo interfaz web...")
        webbrowser.open('http://localhost:8085')
        print("✅ Interfaz web lista")
        print("🎧 Disfruta del prototipo web!")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Cerrando servidor web...")

if __name__ == "__main__":
    main()
