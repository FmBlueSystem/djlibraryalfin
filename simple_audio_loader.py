#!/usr/bin/env python3
"""
🎯 DjAlfin - Simple Audio Loader
Versión ultra-simple que GARANTIZA cargar archivos de /Volumes/KINGSTON/Audio
"""

import tkinter as tk
from tkinter import scrolledtext
import os
import glob
from basic_metadata_reader import BasicMetadataReader

class SimpleAudioLoader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Simple Audio Loader")
        self.root.geometry("1000x600")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.metadata_reader = BasicMetadataReader()
        self.audio_files = []
        self.files_with_cues = []
        
        # Setup UI
        self.setup_ui()
        
        # Load files immediately
        self.load_files_now()
    
    def setup_ui(self):
        """Setup simple UI."""
        
        # Title
        title_label = tk.Label(
            self.root,
            text="🎯 DjAlfin - Audio Files with Cue Points",
            font=('Arial', 16, 'bold'),
            bg='#1a1a1a',
            fg='#58a6ff'
        )
        title_label.pack(pady=10)
        
        # Status
        self.status_label = tk.Label(
            self.root,
            text="📁 Loading files from /Volumes/KINGSTON/Audio...",
            font=('Arial', 12),
            bg='#1a1a1a',
            fg='#f0f6fc'
        )
        self.status_label.pack(pady=5)
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(
            self.root,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 10),
            wrap=tk.WORD,
            height=30
        )
        self.results_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = tk.Frame(self.root, bg='#1a1a1a')
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="🔄 Reload Files",
            command=self.load_files_now,
            bg='#0969da',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="🔍 Scan for Cues",
            command=self.scan_for_cues,
            bg='#238636',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20
        ).pack(side='left', padx=10)
    
    def load_files_now(self):
        """Load audio files immediately."""
        
        self.status_label.config(text="📁 Loading files...")
        self.results_text.delete('1.0', tk.END)
        self.root.update()
        
        audio_folder = "/Volumes/KINGSTON/Audio"
        
        # Check if folder exists
        if not os.path.exists(audio_folder):
            error_msg = f"❌ ERROR: Folder not found: {audio_folder}\n"
            error_msg += f"Please check that the USB drive is connected and mounted.\n"
            self.results_text.insert('1.0', error_msg)
            self.status_label.config(text="❌ Audio folder not found")
            return
        
        # Find audio files
        self.audio_files = []
        extensions = ['.mp3', '.m4a', '.flac', '.wav']
        
        try:
            # List all files in directory
            all_files = os.listdir(audio_folder)
            
            for filename in all_files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                # Check extension
                _, ext = os.path.splitext(filename)
                if ext.lower() in extensions:
                    file_path = os.path.join(audio_folder, filename)
                    
                    try:
                        file_size = os.path.getsize(file_path) / (1024 * 1024)
                        self.audio_files.append({
                            'path': file_path,
                            'filename': filename,
                            'size_mb': file_size,
                            'extension': ext.upper()
                        })
                    except Exception as e:
                        print(f"Error with file {filename}: {e}")
            
            # Display results
            self.display_files()
            
        except Exception as e:
            error_msg = f"❌ ERROR reading folder: {str(e)}\n"
            self.results_text.insert('1.0', error_msg)
            self.status_label.config(text="❌ Error reading folder")
    
    def display_files(self):
        """Display found audio files."""
        
        if not self.audio_files:
            msg = "❌ No audio files found in /Volumes/KINGSTON/Audio\n"
            msg += "Supported formats: MP3, M4A, FLAC, WAV\n"
            self.results_text.insert('1.0', msg)
            self.status_label.config(text="❌ No audio files found")
            return
        
        # Sort files by name
        self.audio_files.sort(key=lambda x: x['filename'])
        
        # Display header
        display_text = f"📁 AUDIO FILES FOUND IN /Volumes/KINGSTON/Audio\n"
        display_text += f"=" * 70 + "\n\n"
        display_text += f"Total files: {len(self.audio_files)}\n\n"
        
        # Display each file
        for i, file_info in enumerate(self.audio_files):
            display_text += f"{i+1:2d}. {file_info['filename']}\n"
            display_text += f"    Size: {file_info['size_mb']:.1f} MB\n"
            display_text += f"    Format: {file_info['extension']}\n"
            display_text += f"    Path: {file_info['path']}\n"
            display_text += "\n"
        
        display_text += f"=" * 70 + "\n"
        display_text += f"✅ Successfully loaded {len(self.audio_files)} audio files\n"
        display_text += f"Click '🔍 Scan for Cues' to check for embedded cue points\n"
        
        self.results_text.insert('1.0', display_text)
        self.status_label.config(text=f"✅ Loaded {len(self.audio_files)} audio files")
        
        print(f"✅ Loaded {len(self.audio_files)} audio files from {audio_folder}")
    
    def scan_for_cues(self):
        """Scan files for embedded cue points."""
        
        if not self.audio_files:
            self.results_text.insert('1.0', "❌ No audio files loaded. Click 'Reload Files' first.\n")
            return
        
        self.status_label.config(text="🔍 Scanning for cue points...")
        self.results_text.delete('1.0', tk.END)
        self.root.update()
        
        # Scan each file
        self.files_with_cues = []
        total_cues = 0
        
        display_text = f"🔍 SCANNING FOR EMBEDDED CUE POINTS\n"
        display_text += f"=" * 70 + "\n\n"
        
        for i, file_info in enumerate(self.audio_files):
            filename = file_info['filename']
            file_path = file_info['path']
            
            # Update status
            self.status_label.config(text=f"🔍 Scanning {i+1}/{len(self.audio_files)}: {filename[:30]}...")
            self.root.update()
            
            display_text += f"{i+1:2d}. {filename}\n"
            
            try:
                # Read metadata
                metadata = self.metadata_reader.scan_file(file_path)
                cue_points = metadata.get('cue_points', [])
                
                if cue_points:
                    software = cue_points[0].software.title()
                    self.files_with_cues.append({
                        **file_info,
                        'cue_points': cue_points,
                        'software': software
                    })
                    total_cues += len(cue_points)
                    
                    display_text += f"    ✅ {len(cue_points)} cue points from {software}\n"
                    
                    # Show first few cue points
                    for j, cue in enumerate(cue_points[:3]):
                        minutes = int(cue.position // 60)
                        seconds = int(cue.position % 60)
                        display_text += f"       {j+1}. {cue.name} @ {minutes}:{seconds:02d} {cue.color}\n"
                    
                    if len(cue_points) > 3:
                        display_text += f"       ... and {len(cue_points) - 3} more\n"
                    
                    print(f"✅ {filename}: {len(cue_points)} cue points from {software}")
                else:
                    display_text += f"    ❌ No cue points found\n"
                
            except Exception as e:
                display_text += f"    ❌ Error: {str(e)}\n"
                print(f"❌ Error scanning {filename}: {e}")
            
            display_text += "\n"
        
        # Summary
        display_text += f"=" * 70 + "\n"
        display_text += f"📊 SCAN RESULTS:\n"
        display_text += f"   Files scanned: {len(self.audio_files)}\n"
        display_text += f"   Files with cue points: {len(self.files_with_cues)}\n"
        display_text += f"   Total cue points found: {total_cues}\n"
        display_text += f"   Success rate: {(len(self.files_with_cues)/len(self.audio_files)*100):.1f}%\n"
        
        if self.files_with_cues:
            display_text += f"\n🎉 SUCCESS! Found embedded cue points!\n"
            display_text += f"Files with cue points:\n"
            for file_info in self.files_with_cues:
                display_text += f"   • {file_info['filename']} ({len(file_info['cue_points'])} cues)\n"
        else:
            display_text += f"\n❌ No embedded cue points found in any file.\n"
            display_text += f"This could mean:\n"
            display_text += f"   • Files haven't been processed by DJ software\n"
            display_text += f"   • Cue points are stored externally\n"
            display_text += f"   • Different metadata format\n"
        
        self.results_text.insert('1.0', display_text)
        
        if self.files_with_cues:
            self.status_label.config(text=f"✅ Found {len(self.files_with_cues)} files with {total_cues} cue points")
        else:
            self.status_label.config(text="❌ No cue points found")
        
        print(f"📊 Scan complete: {len(self.files_with_cues)} files with {total_cues} cue points")
    
    def run(self):
        """Run the application."""
        print("🎯 DjAlfin Simple Audio Loader")
        print("Loading files from /Volumes/KINGSTON/Audio")
        self.root.mainloop()

def main():
    """Main function."""
    try:
        app = SimpleAudioLoader()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
