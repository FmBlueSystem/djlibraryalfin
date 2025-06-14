#!/usr/bin/env python3
"""
🎯 DjAlfin - Audio Analyzer (Fixed Version)
Versión que funciona correctamente en macOS mostrando TODOS los archivos
"""

import tkinter as tk
from tkinter import scrolledtext
import os
import threading
from basic_metadata_reader import BasicMetadataReader

class AudioAnalyzerFixed:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Audio Files Analyzer")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.metadata_reader = BasicMetadataReader()
        self.all_files = []
        self.scanning = False
        
        # Setup UI
        self.setup_ui()
        
        # Start analysis immediately
        self.root.after(1000, self.start_analysis)
    
    def setup_ui(self):
        """Setup user interface."""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#0d1117', height=60)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎯 DjAlfin - Audio Files Analyzer",
            font=('Arial', 16, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(side='left', padx=20, pady=15)
        
        self.status_label = tk.Label(
            header_frame,
            text="🔍 Starting analysis...",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#f85149'
        )
        self.status_label.pack(side='right', padx=20, pady=15)
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - Files list
        self.create_files_panel(main_frame)
        
        # Right panel - Details
        self.create_details_panel(main_frame)
        
        # Bottom panel - Controls
        self.create_controls()
    
    def create_files_panel(self, parent):
        """Create files list panel."""
        
        files_frame = tk.LabelFrame(
            parent,
            text="📁 ALL AUDIO FILES - /Volumes/KINGSTON/Audio",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#58a6ff',
            padx=10,
            pady=10
        )
        files_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Files listbox
        self.files_listbox = tk.Listbox(
            files_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            selectbackground='#58a6ff',
            font=('Courier', 9),
            height=30
        )
        self.files_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind selection
        self.files_listbox.bind('<ButtonRelease-1>', self.on_file_select)
    
    def create_details_panel(self, parent):
        """Create details panel."""
        
        details_frame = tk.LabelFrame(
            parent,
            text="📊 Analysis Results & File Details",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#58a6ff',
            padx=10,
            pady=10
        )
        details_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Summary
        self.summary_text = tk.Text(
            details_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 10),
            height=8,
            wrap=tk.WORD
        )
        self.summary_text.pack(fill='x', padx=5, pady=(0, 10))
        
        # File details
        self.details_text = scrolledtext.ScrolledText(
            details_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 9),
            wrap=tk.WORD
        )
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize
        self.summary_text.insert('1.0', "🔍 Starting analysis of /Volumes/KINGSTON/Audio...")
        self.details_text.insert('1.0', "Select a file from the list to view details")
    
    def create_controls(self):
        """Create control buttons."""
        
        control_frame = tk.Frame(self.root, bg='#0d1117', height=50)
        control_frame.pack(fill='x', padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        tk.Button(
            control_frame,
            text="🔄 Rescan All",
            command=self.start_analysis,
            bg='#0969da',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15
        ).pack(side='left', padx=10, pady=10)
        
        tk.Button(
            control_frame,
            text="✅ With Cues Only",
            command=self.show_with_cues_only,
            bg='#238636',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15
        ).pack(side='left', padx=10, pady=10)
        
        tk.Button(
            control_frame,
            text="📁 Show All",
            command=self.show_all_files,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15
        ).pack(side='left', padx=10, pady=10)
    
    def start_analysis(self):
        """Start analyzing all files."""
        
        if self.scanning:
            return
        
        self.scanning = True
        self.status_label.config(text="🔍 Analyzing all audio files...", fg='#f85149')
        
        # Clear displays
        self.files_listbox.delete(0, tk.END)
        self.summary_text.delete('1.0', tk.END)
        self.details_text.delete('1.0', tk.END)
        
        self.summary_text.insert('1.0', "🔍 Scanning /Volumes/KINGSTON/Audio...\nPlease wait...")
        self.details_text.insert('1.0', "Analysis in progress...")
        
        self.all_files = []
        
        # Start analysis thread
        threading.Thread(target=self.analyze_all_files, daemon=True).start()
    
    def analyze_all_files(self):
        """Analyze all audio files."""
        
        audio_folder = "/Volumes/KINGSTON/Audio"
        
        if not os.path.exists(audio_folder):
            self.root.after(0, lambda: self.status_label.config(
                text="❌ Audio folder not found", fg='#f85149'
            ))
            self.scanning = False
            return
        
        try:
            # Get all audio files
            all_items = os.listdir(audio_folder)
            audio_extensions = ['.mp3', '.m4a', '.flac', '.wav']
            
            audio_files = []
            for item in all_items:
                if not item.startswith('.'):  # Skip hidden files
                    _, ext = os.path.splitext(item)
                    if ext.lower() in audio_extensions:
                        audio_files.append(item)
            
            audio_files.sort()  # Sort alphabetically
            
            print(f"🔍 Found {len(audio_files)} audio files to analyze")
            
            # Analyze each file
            for i, filename in enumerate(audio_files):
                file_path = os.path.join(audio_folder, filename)
                
                # Update status
                self.root.after(0, lambda f=filename, i=i, t=len(audio_files): 
                    self.status_label.config(text=f"🔍 Analyzing {i+1}/{t}: {f[:25]}...")
                )
                
                try:
                    # Get basic file info
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    _, ext = os.path.splitext(filename)
                    format_name = ext.upper().replace('.', '')
                    
                    # Analyze for cue points
                    metadata = self.metadata_reader.scan_file(file_path)
                    cue_points = metadata.get('cue_points', [])
                    
                    # Create file info
                    file_info = {
                        'filename': filename,
                        'path': file_path,
                        'size_mb': file_size,
                        'format': format_name,
                        'has_cues': len(cue_points) > 0,
                        'cue_count': len(cue_points),
                        'software': cue_points[0].software.title() if cue_points else 'None',
                        'cue_points': cue_points,
                        'metadata': metadata
                    }
                    
                    self.all_files.append(file_info)
                    
                    # Add to display
                    status_icon = "✅" if file_info['has_cues'] else "❌"
                    display_line = f"{status_icon} {filename} ({file_info['size_mb']:.1f}MB, {format_name}"
                    
                    if file_info['has_cues']:
                        display_line += f", {file_info['cue_count']} cues, {file_info['software']})"
                        print(f"✅ {filename}: {len(cue_points)} cue points from {file_info['software']}")
                    else:
                        display_line += ", No cues)"
                    
                    # Add to listbox
                    self.root.after(0, lambda line=display_line: 
                        self.files_listbox.insert(tk.END, line)
                    )
                    
                except Exception as e:
                    print(f"❌ Error analyzing {filename}: {e}")
                    
                    # Add error entry
                    file_info = {
                        'filename': filename,
                        'path': file_path,
                        'size_mb': file_size if 'file_size' in locals() else 0,
                        'format': format_name if 'format_name' in locals() else 'Unknown',
                        'has_cues': False,
                        'cue_count': 0,
                        'software': 'Error',
                        'cue_points': [],
                        'error': str(e)
                    }
                    
                    self.all_files.append(file_info)
                    
                    display_line = f"❌ {filename} (Error: {str(e)[:30]}...)"
                    self.root.after(0, lambda line=display_line: 
                        self.files_listbox.insert(tk.END, line)
                    )
            
            # Update summary
            self.root.after(0, self.update_summary)
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            self.root.after(0, lambda: self.status_label.config(
                text=f"❌ Analysis error: {str(e)}", fg='#f85149'
            ))
        
        self.scanning = False
    
    def update_summary(self):
        """Update summary statistics."""
        
        total_files = len(self.all_files)
        files_with_cues = len([f for f in self.all_files if f['has_cues']])
        total_cues = sum(f['cue_count'] for f in self.all_files)
        
        # Create summary
        summary = f"📊 ANALYSIS COMPLETE\n"
        summary += f"=" * 40 + "\n"
        summary += f"📁 Total audio files: {total_files}\n"
        summary += f"✅ Files WITH cue points: {files_with_cues}\n"
        summary += f"❌ Files WITHOUT cues: {total_files - files_with_cues}\n"
        summary += f"🎯 Total cue points found: {total_cues}\n"
        summary += f"📈 Success rate: {(files_with_cues/total_files*100):.1f}%\n\n"
        
        # Format breakdown
        format_stats = {}
        for file_info in self.all_files:
            fmt = file_info['format']
            if fmt not in format_stats:
                format_stats[fmt] = {'total': 0, 'with_cues': 0}
            format_stats[fmt]['total'] += 1
            if file_info['has_cues']:
                format_stats[fmt]['with_cues'] += 1
        
        summary += f"📊 BY FORMAT:\n"
        for fmt, stats in format_stats.items():
            rate = (stats['with_cues']/stats['total']*100) if stats['total'] > 0 else 0
            summary += f"   {fmt}: {stats['with_cues']}/{stats['total']} ({rate:.1f}%)\n"
        
        # Software stats
        software_files = [f for f in self.all_files if f['has_cues']]
        if software_files:
            summary += f"\n🎛️ SOFTWARE DETECTED:\n"
            software_stats = {}
            for f in software_files:
                sw = f['software']
                if sw not in software_stats:
                    software_stats[sw] = 0
                software_stats[sw] += 1
            
            for software, count in software_stats.items():
                summary += f"   {software}: {count} files\n"
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary)
        
        # Update status
        if files_with_cues > 0:
            self.status_label.config(
                text=f"✅ Found {files_with_cues} files with {total_cues} cue points",
                fg='#238636'
            )
        else:
            self.status_label.config(
                text=f"❌ No cue points found in {total_files} files",
                fg='#f85149'
            )
        
        print(f"📊 Analysis complete: {files_with_cues}/{total_files} files with {total_cues} cue points")
    
    def on_file_select(self, event):
        """Handle file selection."""
        
        selection = self.files_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if 0 <= index < len(self.all_files):
            file_info = self.all_files[index]
            self.show_file_details(file_info)
    
    def show_file_details(self, file_info):
        """Show detailed file information."""
        
        details = f"📁 FILE DETAILS\n"
        details += f"=" * 50 + "\n"
        details += f"📄 Filename: {file_info['filename']}\n"
        details += f"📊 Size: {file_info['size_mb']:.1f} MB\n"
        details += f"🎵 Format: {file_info['format']}\n"
        details += f"📍 Full path: {file_info['path']}\n\n"
        
        if file_info['has_cues']:
            details += f"🎯 CUE POINTS FOUND: {file_info['cue_count']}\n"
            details += f"🎛️ Software: {file_info['software']}\n"
            details += f"=" * 50 + "\n\n"
            
            for i, cue in enumerate(file_info['cue_points']):
                minutes = int(cue.position // 60)
                seconds = int(cue.position % 60)
                
                details += f"{i+1:2d}. {cue.name}\n"
                details += f"    ⏰ Time: {minutes}:{seconds:02d} ({cue.position:.1f}s)\n"
                details += f"    🎨 Color: {cue.color}\n"
                details += f"    🔥 Hot Cue: #{cue.hotcue_index}\n"
                details += f"    ⚡ Energy: {cue.energy_level}/10\n"
                details += f"    🎛️ Source: {cue.software}\n\n"
        else:
            details += f"❌ NO CUE POINTS FOUND\n"
            details += f"=" * 50 + "\n"
            if 'error' in file_info:
                details += f"🚨 Error during analysis: {file_info['error']}\n"
            else:
                details += f"This file has not been processed by DJ software\n"
                details += f"or cue points are stored in external files.\n\n"
                details += f"Supported DJ software:\n"
                details += f"   • Serato DJ\n"
                details += f"   • Mixed In Key\n"
                details += f"   • Traktor Pro\n"
                details += f"   • Pioneer Rekordbox\n"
        
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', details)
    
    def show_with_cues_only(self):
        """Show only files with cue points."""
        
        self.files_listbox.delete(0, tk.END)
        
        for file_info in self.all_files:
            if file_info['has_cues']:
                display_line = f"✅ {file_info['filename']} ({file_info['size_mb']:.1f}MB, {file_info['format']}, {file_info['cue_count']} cues, {file_info['software']})"
                self.files_listbox.insert(tk.END, display_line)
    
    def show_all_files(self):
        """Show all files."""
        
        self.files_listbox.delete(0, tk.END)
        
        for file_info in self.all_files:
            status_icon = "✅" if file_info['has_cues'] else "❌"
            display_line = f"{status_icon} {file_info['filename']} ({file_info['size_mb']:.1f}MB, {file_info['format']}"
            
            if file_info['has_cues']:
                display_line += f", {file_info['cue_count']} cues, {file_info['software']})"
            else:
                display_line += ", No cues)"
            
            self.files_listbox.insert(tk.END, display_line)
    
    def run(self):
        """Run the application."""
        print("🎯 DjAlfin Audio Files Analyzer (Fixed)")
        print("Analyzing ALL files in /Volumes/KINGSTON/Audio")
        self.root.mainloop()

def main():
    """Main function."""
    try:
        app = AudioAnalyzerFixed()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
