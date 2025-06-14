#!/usr/bin/env python3
"""
🎯 DjAlfin - Audio Viewer Simple
Versión SIN THREADING que GARANTIZA mostrar los archivos
"""

import tkinter as tk
from tkinter import scrolledtext
import os
from basic_metadata_reader import BasicMetadataReader

class AudioViewerSimple:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Audio Viewer")
        self.root.geometry("1000x600")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.metadata_reader = BasicMetadataReader()
        self.all_files = []
        
        # Setup UI
        self.setup_ui()
        
        # Load files IMMEDIATELY without threading
        self.load_files_now()
    
    def setup_ui(self):
        """Setup simple UI."""
        
        # Title
        title_label = tk.Label(
            self.root,
            text="🎯 DjAlfin - Audio Files Viewer",
            font=('Arial', 16, 'bold'),
            bg='#1a1a1a',
            fg='#58a6ff'
        )
        title_label.pack(pady=10)
        
        # Status
        self.status_label = tk.Label(
            self.root,
            text="📁 Loading files...",
            font=('Arial', 12),
            bg='#1a1a1a',
            fg='#f0f6fc'
        )
        self.status_label.pack(pady=5)
        
        # Main display
        self.display_text = scrolledtext.ScrolledText(
            self.root,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 10),
            wrap=tk.WORD
        )
        self.display_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = tk.Frame(self.root, bg='#1a1a1a')
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="🔄 Reload",
            command=self.load_files_now,
            bg='#0969da',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="🎯 Analyze Cues",
            command=self.analyze_cues_now,
            bg='#238636',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20
        ).pack(side='left', padx=10)
    
    def load_files_now(self):
        """Load files immediately WITHOUT threading."""
        
        self.status_label.config(text="📁 Loading files...")
        self.display_text.delete('1.0', tk.END)
        self.root.update()  # Force UI update
        
        audio_folder = "/Volumes/KINGSTON/Audio"
        
        # Check folder
        if not os.path.exists(audio_folder):
            error_msg = f"❌ ERROR: Folder not found\n{audio_folder}\n\n"
            error_msg += "Please check:\n"
            error_msg += "1. USB drive is connected\n"
            error_msg += "2. Drive is mounted\n"
            error_msg += "3. Path is correct\n"
            
            self.display_text.insert('1.0', error_msg)
            self.status_label.config(text="❌ Folder not found")
            return
        
        # Load files
        try:
            all_items = os.listdir(audio_folder)
            audio_extensions = ['.mp3', '.m4a', '.flac', '.wav']
            
            self.all_files = []
            
            for item in all_items:
                if not item.startswith('.'):  # Skip hidden files
                    _, ext = os.path.splitext(item)
                    if ext.lower() in audio_extensions:
                        file_path = os.path.join(audio_folder, item)
                        
                        try:
                            file_size = os.path.getsize(file_path) / (1024 * 1024)
                            
                            file_info = {
                                'filename': item,
                                'path': file_path,
                                'size_mb': file_size,
                                'format': ext.upper().replace('.', ''),
                                'analyzed': False
                            }
                            
                            self.all_files.append(file_info)
                            
                        except Exception as e:
                            print(f"Error with {item}: {e}")
            
            # Sort files
            self.all_files.sort(key=lambda x: x['filename'])
            
            # Display files
            self.display_files()
            
        except Exception as e:
            error_msg = f"❌ ERROR loading files: {str(e)}\n"
            self.display_text.insert('1.0', error_msg)
            self.status_label.config(text="❌ Error loading files")
    
    def display_files(self):
        """Display all files immediately."""
        
        if not self.all_files:
            msg = "❌ No audio files found\n"
            self.display_text.insert('1.0', msg)
            self.status_label.config(text="❌ No files found")
            return
        
        # Create display
        display_text = f"📁 AUDIO FILES IN /Volumes/KINGSTON/Audio\n"
        display_text += f"=" * 70 + "\n\n"
        display_text += f"Found {len(self.all_files)} audio files:\n\n"
        
        for i, file_info in enumerate(self.all_files):
            display_text += f"{i+1:2d}. {file_info['filename']}\n"
            display_text += f"    📊 Size: {file_info['size_mb']:.1f} MB\n"
            display_text += f"    🎵 Format: {file_info['format']}\n"
            display_text += f"    📍 Path: {file_info['path']}\n"
            
            if file_info.get('analyzed', False):
                if file_info.get('has_cues', False):
                    display_text += f"    ✅ Cue Points: {file_info['cue_count']} from {file_info['software']}\n"
                else:
                    display_text += f"    ❌ No cue points found\n"
            else:
                display_text += f"    🔍 Not analyzed yet\n"
            
            display_text += "\n"
        
        display_text += f"=" * 70 + "\n"
        display_text += f"✅ Successfully loaded {len(self.all_files)} files\n"
        display_text += f"Click '🎯 Analyze Cues' to check for embedded cue points\n"
        
        # Show in display
        self.display_text.delete('1.0', tk.END)
        self.display_text.insert('1.0', display_text)
        
        self.status_label.config(text=f"✅ Loaded {len(self.all_files)} audio files")
        
        print(f"✅ Displayed {len(self.all_files)} files in GUI")
    
    def analyze_cues_now(self):
        """Analyze cues immediately WITHOUT threading."""
        
        if not self.all_files:
            self.display_text.insert('1.0', "❌ No files loaded. Click 'Reload' first.\n")
            return
        
        self.status_label.config(text="🔍 Analyzing cue points...")
        self.display_text.delete('1.0', tk.END)
        self.root.update()
        
        # Analyze each file
        files_with_cues = 0
        total_cues = 0
        
        display_text = f"🔍 CUE POINTS ANALYSIS\n"
        display_text += f"=" * 70 + "\n\n"
        
        for i, file_info in enumerate(self.all_files):
            filename = file_info['filename']
            file_path = file_info['path']
            
            # Update status
            self.status_label.config(text=f"🔍 Analyzing {i+1}/{len(self.all_files)}: {filename[:25]}...")
            self.root.update()
            
            display_text += f"{i+1:2d}. {filename}\n"
            
            try:
                # Analyze for cue points
                metadata = self.metadata_reader.scan_file(file_path)
                cue_points = metadata.get('cue_points', [])
                
                # Update file info
                file_info['analyzed'] = True
                file_info['has_cues'] = len(cue_points) > 0
                file_info['cue_count'] = len(cue_points)
                file_info['cue_points'] = cue_points
                
                if cue_points:
                    software = cue_points[0].software.title()
                    file_info['software'] = software
                    
                    files_with_cues += 1
                    total_cues += len(cue_points)
                    
                    display_text += f"    ✅ {len(cue_points)} cue points from {software}\n"
                    
                    # Show first few cue points
                    for j, cue in enumerate(cue_points[:3]):
                        minutes = int(cue.position // 60)
                        seconds = int(cue.position % 60)
                        display_text += f"       {j+1}. {cue.name} @ {minutes}:{seconds:02d} {cue.color}\n"
                    
                    if len(cue_points) > 3:
                        display_text += f"       ... and {len(cue_points) - 3} more\n"
                    
                    print(f"✅ {filename}: {len(cue_points)} cue points")
                else:
                    file_info['software'] = 'None'
                    display_text += f"    ❌ No cue points found\n"
                
            except Exception as e:
                file_info['analyzed'] = True
                file_info['has_cues'] = False
                file_info['error'] = str(e)
                
                display_text += f"    ❌ Error: {str(e)}\n"
                print(f"❌ Error analyzing {filename}: {e}")
            
            display_text += "\n"
        
        # Summary
        display_text += f"=" * 70 + "\n"
        display_text += f"📊 ANALYSIS RESULTS:\n"
        display_text += f"   Files analyzed: {len(self.all_files)}\n"
        display_text += f"   Files with cue points: {files_with_cues}\n"
        display_text += f"   Total cue points found: {total_cues}\n"
        display_text += f"   Success rate: {(files_with_cues/len(self.all_files)*100):.1f}%\n\n"
        
        if files_with_cues > 0:
            display_text += f"🎉 SUCCESS! Found embedded cue points!\n"
            display_text += f"Files with cue points:\n"
            for file_info in self.all_files:
                if file_info.get('has_cues', False):
                    display_text += f"   • {file_info['filename']} ({file_info['cue_count']} cues)\n"
        else:
            display_text += f"❌ No embedded cue points found.\n"
        
        # Show results
        self.display_text.delete('1.0', tk.END)
        self.display_text.insert('1.0', display_text)
        
        if files_with_cues > 0:
            self.status_label.config(text=f"✅ Found {files_with_cues} files with {total_cues} cue points")
        else:
            self.status_label.config(text="❌ No cue points found")
        
        print(f"📊 Analysis complete: {files_with_cues} files with {total_cues} cue points")
    
    def run(self):
        """Run the application."""
        print("🎯 DjAlfin Audio Viewer Simple")
        print("Loading files WITHOUT threading")
        self.root.mainloop()

def main():
    """Main function."""
    try:
        app = AudioViewerSimple()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
