#!/usr/bin/env python3
"""
🎯 DjAlfin - Audio Files Analyzer
Muestra TODOS los archivos y determina cuáles tienen cue points
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import threading
from basic_metadata_reader import BasicMetadataReader

class AudioFilesAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Audio Files Analyzer")
        self.root.geometry("1400x800")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.metadata_reader = BasicMetadataReader()
        self.all_files = []
        self.scanning = False
        
        # Setup UI
        self.setup_ui()
        
        # Start automatic scan
        self.root.after(500, self.start_analysis)
    
    def setup_ui(self):
        """Setup user interface."""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#0d1117', height=70)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎯 DjAlfin - Audio Files Analyzer",
            font=('Arial', 18, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(side='left', padx=20, pady=20)
        
        self.status_label = tk.Label(
            header_frame,
            text="🔍 Starting analysis...",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#f85149'
        )
        self.status_label.pack(side='right', padx=20, pady=20)
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Files table
        self.create_files_table(main_frame)
        
        # Summary panel
        self.create_summary_panel(main_frame)
        
        # Control buttons
        self.create_controls()
    
    def create_files_table(self, parent):
        """Create files table with cue point status."""
        
        table_frame = tk.LabelFrame(
            parent,
            text="📁 ALL AUDIO FILES - /Volumes/KINGSTON/Audio",
            font=('Arial', 14, 'bold'),
            bg='#21262d',
            fg='#58a6ff',
            padx=15,
            pady=15
        )
        table_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Create treeview
        columns = ('Status', 'Filename', 'Size', 'Format', 'Cues', 'Software')
        self.files_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=25
        )
        
        # Configure columns
        self.files_tree.heading('Status', text='Status')
        self.files_tree.heading('Filename', text='Filename')
        self.files_tree.heading('Size', text='Size (MB)')
        self.files_tree.heading('Format', text='Format')
        self.files_tree.heading('Cues', text='Cues')
        self.files_tree.heading('Software', text='Software')
        
        self.files_tree.column('Status', width=60)
        self.files_tree.column('Filename', width=400)
        self.files_tree.column('Size', width=80)
        self.files_tree.column('Format', width=60)
        self.files_tree.column('Cues', width=50)
        self.files_tree.column('Software', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        self.files_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind selection
        self.files_tree.bind('<ButtonRelease-1>', self.on_file_select)
    
    def create_summary_panel(self, parent):
        """Create summary and details panel."""
        
        summary_frame = tk.LabelFrame(
            parent,
            text="📊 Analysis Summary & Details",
            font=('Arial', 14, 'bold'),
            bg='#21262d',
            fg='#58a6ff',
            padx=15,
            pady=15
        )
        summary_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Summary stats
        self.summary_text = tk.Text(
            summary_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 11),
            height=8,
            wrap=tk.WORD
        )
        self.summary_text.pack(fill='x', padx=5, pady=(0, 10))
        
        # File details
        tk.Label(
            summary_frame,
            text="🎯 Selected File Details:",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc'
        ).pack(anchor='w', padx=5)
        
        self.details_text = scrolledtext.ScrolledText(
            summary_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 10),
            wrap=tk.WORD
        )
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize displays
        self.summary_text.insert('1.0', "🔍 Starting analysis of audio files...")
        self.details_text.insert('1.0', "Select a file from the table to view details")
    
    def create_controls(self):
        """Create control buttons."""
        
        control_frame = tk.Frame(self.root, bg='#0d1117', height=60)
        control_frame.pack(fill='x', padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        tk.Button(
            control_frame,
            text="🔄 Rescan All Files",
            command=self.start_analysis,
            bg='#0969da',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20
        ).pack(side='left', padx=10, pady=15)
        
        tk.Button(
            control_frame,
            text="✅ Show Only With Cues",
            command=self.filter_with_cues,
            bg='#238636',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20
        ).pack(side='left', padx=10, pady=15)
        
        tk.Button(
            control_frame,
            text="📁 Show All Files",
            command=self.show_all_files,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20
        ).pack(side='left', padx=10, pady=15)
    
    def start_analysis(self):
        """Start analyzing all audio files."""
        
        if self.scanning:
            return
        
        self.scanning = True
        self.status_label.config(text="🔍 Analyzing all audio files...", fg='#f85149')
        
        # Clear table
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        self.all_files = []
        
        # Start analysis thread
        threading.Thread(target=self.analyze_files, daemon=True).start()
    
    def analyze_files(self):
        """Analyze all audio files for cue points."""
        
        audio_folder = "/Volumes/KINGSTON/Audio"
        
        if not os.path.exists(audio_folder):
            self.root.after(0, lambda: self.status_label.config(
                text="❌ Audio folder not found", fg='#f85149'
            ))
            self.scanning = False
            return
        
        try:
            # Get all files
            all_items = os.listdir(audio_folder)
            audio_extensions = ['.mp3', '.m4a', '.flac', '.wav']
            
            audio_files = []
            for item in all_items:
                if not item.startswith('.'):  # Skip hidden files
                    _, ext = os.path.splitext(item)
                    if ext.lower() in audio_extensions:
                        audio_files.append(item)
            
            print(f"🔍 Found {len(audio_files)} audio files to analyze")
            
            # Analyze each file
            for i, filename in enumerate(audio_files):
                file_path = os.path.join(audio_folder, filename)
                
                # Update status
                self.root.after(0, lambda f=filename, i=i, t=len(audio_files): 
                    self.status_label.config(text=f"🔍 Analyzing {i+1}/{t}: {f[:30]}...")
                )
                
                try:
                    # Get file info
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    _, ext = os.path.splitext(filename)
                    format_name = ext.upper().replace('.', '')
                    
                    # Read metadata for cue points
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
                    
                    # Add to table in real-time
                    status_icon = "✅" if file_info['has_cues'] else "❌"
                    cue_text = str(file_info['cue_count']) if file_info['has_cues'] else "0"
                    
                    self.root.after(0, lambda info=file_info, status=status_icon, cues=cue_text:
                        self.files_tree.insert('', 'end', values=(
                            status,
                            info['filename'],
                            f"{info['size_mb']:.1f}",
                            info['format'],
                            cues,
                            info['software']
                        ))
                    )
                    
                    if file_info['has_cues']:
                        print(f"✅ {filename}: {len(cue_points)} cue points from {file_info['software']}")
                    
                except Exception as e:
                    print(f"❌ Error analyzing {filename}: {e}")
                    
                    # Add error entry
                    file_info = {
                        'filename': filename,
                        'path': file_path,
                        'size_mb': 0,
                        'format': ext.upper().replace('.', '') if ext else 'Unknown',
                        'has_cues': False,
                        'cue_count': 0,
                        'software': 'Error',
                        'cue_points': [],
                        'metadata': {},
                        'error': str(e)
                    }
                    
                    self.all_files.append(file_info)
                    
                    self.root.after(0, lambda info=file_info:
                        self.files_tree.insert('', 'end', values=(
                            "❌",
                            info['filename'],
                            "Error",
                            info['format'],
                            "0",
                            "Error"
                        ))
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
        
        # Software statistics
        software_stats = {}
        for file_info in self.all_files:
            if file_info['has_cues']:
                software = file_info['software']
                if software not in software_stats:
                    software_stats[software] = {'files': 0, 'cues': 0}
                software_stats[software]['files'] += 1
                software_stats[software]['cues'] += file_info['cue_count']
        
        # Format statistics
        format_stats = {}
        for file_info in self.all_files:
            fmt = file_info['format']
            if fmt not in format_stats:
                format_stats[fmt] = {'total': 0, 'with_cues': 0}
            format_stats[fmt]['total'] += 1
            if file_info['has_cues']:
                format_stats[fmt]['with_cues'] += 1
        
        # Create summary text
        summary = f"📊 ANALYSIS SUMMARY\n"
        summary += f"=" * 40 + "\n"
        summary += f"📁 Total audio files: {total_files}\n"
        summary += f"✅ Files with cue points: {files_with_cues}\n"
        summary += f"❌ Files without cues: {total_files - files_with_cues}\n"
        summary += f"🎯 Total cue points: {total_cues}\n"
        summary += f"📈 Success rate: {(files_with_cues/total_files*100):.1f}%\n\n"
        
        if software_stats:
            summary += f"🎛️ SOFTWARE DETECTED:\n"
            for software, stats in software_stats.items():
                summary += f"   {software}: {stats['files']} files, {stats['cues']} cues\n"
            summary += "\n"
        
        summary += f"📊 BY FORMAT:\n"
        for fmt, stats in format_stats.items():
            rate = (stats['with_cues']/stats['total']*100) if stats['total'] > 0 else 0
            summary += f"   {fmt}: {stats['with_cues']}/{stats['total']} ({rate:.1f}%)\n"
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary)
        
        # Update status
        if files_with_cues > 0:
            self.status_label.config(
                text=f"✅ Analysis complete: {files_with_cues} files with {total_cues} cue points",
                fg='#238636'
            )
        else:
            self.status_label.config(
                text=f"❌ Analysis complete: No cue points found in {total_files} files",
                fg='#f85149'
            )
        
        print(f"📊 Analysis complete: {files_with_cues}/{total_files} files with {total_cues} cue points")
    
    def on_file_select(self, event):
        """Handle file selection."""
        
        selection = self.files_tree.selection()
        if not selection:
            return
        
        # Get selected item
        item = selection[0]
        index = self.files_tree.index(item)
        
        if 0 <= index < len(self.all_files):
            file_info = self.all_files[index]
            self.show_file_details(file_info)
    
    def show_file_details(self, file_info):
        """Show detailed information about selected file."""
        
        details = f"📁 FILE DETAILS\n"
        details += f"=" * 50 + "\n"
        details += f"📄 Filename: {file_info['filename']}\n"
        details += f"📊 Size: {file_info['size_mb']:.1f} MB\n"
        details += f"🎵 Format: {file_info['format']}\n"
        details += f"📍 Path: {file_info['path']}\n\n"
        
        if file_info['has_cues']:
            details += f"🎯 CUE POINTS: {file_info['cue_count']}\n"
            details += f"🎛️ Software: {file_info['software']}\n"
            details += f"=" * 50 + "\n\n"
            
            for i, cue in enumerate(file_info['cue_points']):
                minutes = int(cue.position // 60)
                seconds = int(cue.position % 60)
                
                details += f"{i+1:2d}. {cue.name}\n"
                details += f"    ⏰ Time: {minutes}:{seconds:02d} ({cue.position:.1f}s)\n"
                details += f"    🎨 Color: {cue.color}\n"
                details += f"    🔥 Hot Cue: #{cue.hotcue_index}\n"
                details += f"    ⚡ Energy: {cue.energy_level}/10\n\n"
        else:
            details += f"❌ NO CUE POINTS FOUND\n"
            if 'error' in file_info:
                details += f"🚨 Error: {file_info['error']}\n"
            else:
                details += f"This file has not been processed by DJ software\n"
                details += f"or cue points are stored externally.\n"
        
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', details)
    
    def filter_with_cues(self):
        """Show only files with cue points."""
        
        # Clear table
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Add only files with cues
        for file_info in self.all_files:
            if file_info['has_cues']:
                self.files_tree.insert('', 'end', values=(
                    "✅",
                    file_info['filename'],
                    f"{file_info['size_mb']:.1f}",
                    file_info['format'],
                    str(file_info['cue_count']),
                    file_info['software']
                ))
    
    def show_all_files(self):
        """Show all files."""
        
        # Clear table
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Add all files
        for file_info in self.all_files:
            status_icon = "✅" if file_info['has_cues'] else "❌"
            cue_text = str(file_info['cue_count']) if file_info['has_cues'] else "0"
            
            self.files_tree.insert('', 'end', values=(
                status_icon,
                file_info['filename'],
                f"{file_info['size_mb']:.1f}",
                file_info['format'],
                cue_text,
                file_info['software']
            ))
    
    def run(self):
        """Run the application."""
        print("🎯 DjAlfin Audio Files Analyzer")
        print("Analyzing ALL files in /Volumes/KINGSTON/Audio")
        self.root.mainloop()

def main():
    """Main function."""
    try:
        app = AudioFilesAnalyzer()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
