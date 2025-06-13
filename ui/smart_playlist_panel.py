"""
Enhanced Smart Playlist Panel for DjAlfin
UI component for creating and managing smart playlists with advanced features.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Dict, Any
from core.smart_playlist_manager import (
    SmartPlaylistManager, SmartPlaylist, PlaylistRule, 
    PlaylistCriteria, ComparisonOperator, PREDEFINED_PLAYLISTS
)
from ui.advanced_smart_playlist_dialog import AdvancedSmartPlaylistDialog, SimpleSmartPlaylistDialog


class SmartPlaylistPanel(ttk.Frame):
    """Enhanced panel for managing smart playlists."""
    
    def __init__(self, master: tk.Widget, db_manager, play_track_callback: Callable[[str], None]):
        super().__init__(master)
        self.db_manager = db_manager
        self.play_track_callback = play_track_callback
        self.smart_playlist_manager = SmartPlaylistManager(db_manager.db_path)
        
        self._create_widgets()
        self._load_smart_playlists()
        self._create_predefined_playlists()
    
    def _create_widgets(self) -> None:
        """Create the UI widgets."""
        # Create main paned window for better layout
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True)
        
        # Left panel - Playlist management
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Track display and details
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        self._create_left_panel(left_frame)
        self._create_right_panel(right_frame)
    
    def _create_left_panel(self, parent: ttk.Frame) -> None:
        """Create the left panel with playlist management."""
        # Title
        title_label = ttk.Label(parent, text="🎵 Smart Playlists", font=("Helvetica", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Search/Filter
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(search_frame, text="Filter:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Playlist list with enhanced display
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="both", expand=True)
        
        # Enhanced treeview for playlists
        self.playlist_tree = ttk.Treeview(
            list_frame,
            columns=("rules", "tracks", "updated"),
            show="tree headings",
            height=12
        )
        
        self.playlist_tree.heading("#0", text="Playlist Name")
        self.playlist_tree.heading("rules", text="Rules")
        self.playlist_tree.heading("tracks", text="Tracks")
        self.playlist_tree.heading("updated", text="Updated")
        
        self.playlist_tree.column("#0", width=180)
        self.playlist_tree.column("rules", width=50)
        self.playlist_tree.column("tracks", width=50)
        self.playlist_tree.column("updated", width=80)
        
        # Scrollbar for playlist tree
        playlist_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.playlist_tree.yview)
        self.playlist_tree.configure(yscrollcommand=playlist_scrollbar.set)
        
        self.playlist_tree.pack(side="left", fill="both", expand=True)
        playlist_scrollbar.pack(side="right", fill="y")
        
        # Bind events
        self.playlist_tree.bind("<<TreeviewSelect>>", self._on_playlist_select)
        self.playlist_tree.bind("<Double-Button-1>", self._on_playlist_double_click)
        self.playlist_tree.bind("<Button-3>", self._on_playlist_right_click)  # Right-click menu
        
        # Buttons frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Create buttons in a grid for better organization
        ttk.Button(
            button_frame, 
            text="🎵 Generate", 
            command=self._generate_selected_playlist,
            state="disabled"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        self.generate_button = button_frame.grid_slaves(row=0, column=0)[0]
        
        ttk.Button(
            button_frame, 
            text="➕ Quick Create", 
            command=self._create_quick_playlist
        ).grid(row=0, column=1, sticky="ew", padx=2)
        
        ttk.Button(
            button_frame, 
            text="⚙️ Advanced", 
            command=self._create_advanced_playlist
        ).grid(row=1, column=0, sticky="ew", padx=(0, 2), pady=(2, 0))
        
        ttk.Button(
            button_frame, 
            text="🗑️ Delete", 
            command=self._delete_selected_playlist,
            state="disabled"
        ).grid(row=1, column=1, sticky="ew", padx=2, pady=(2, 0))
        self.delete_button = button_frame.grid_slaves(row=1, column=1)[0]
        
        # Configure grid weights
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding=5)
        stats_frame.pack(fill="x", pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="No playlist selected")
        self.stats_label.pack()
    
    def _create_right_panel(self, parent: ttk.Frame) -> None:
        """Create the right panel with track display and details."""
        # Notebook for different views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)
        
        # Generated tracks tab
        tracks_frame = ttk.Frame(notebook)
        notebook.add(tracks_frame, text="🎵 Generated Tracks")
        
        # Tracks treeview with enhanced columns
        self.tracks_tree = ttk.Treeview(
            tracks_frame,
            columns=("artist", "title", "album", "genre", "year", "bpm", "duration", "plays"),
            show="headings",
            height=15
        )
        
        # Configure columns
        columns_config = {
            "artist": ("Artist", 120),
            "title": ("Title", 150),
            "album": ("Album", 120),
            "genre": ("Genre", 80),
            "year": ("Year", 60),
            "bpm": ("BPM", 60),
            "duration": ("Duration", 70),
            "plays": ("Plays", 50)
        }
        
        for col, (text, width) in columns_config.items():
            self.tracks_tree.heading(col, text=text)
            self.tracks_tree.column(col, width=width)
        
        # Tracks scrollbar
        tracks_scrollbar = ttk.Scrollbar(tracks_frame, orient="vertical", command=self.tracks_tree.yview)
        self.tracks_tree.configure(yscrollcommand=tracks_scrollbar.set)
        
        self.tracks_tree.pack(side="left", fill="both", expand=True)
        tracks_scrollbar.pack(side="right", fill="y")
        
        # Bind double-click to play track
        self.tracks_tree.bind("<Double-Button-1>", self._on_track_double_click)
        self.tracks_tree.bind("<Button-3>", self._on_track_right_click)
        
        # Track controls
        track_controls = ttk.Frame(tracks_frame)
        track_controls.pack(fill="x", pady=(5, 0))
        
        ttk.Button(track_controls, text="▶️ Play Selected", command=self._play_selected_track).pack(side="left", padx=(0, 5))
        ttk.Button(track_controls, text="📋 Export List", command=self._export_playlist).pack(side="left", padx=5)
        ttk.Button(track_controls, text="🔄 Refresh", command=self._refresh_current_playlist).pack(side="left", padx=5)
        
        # Playlist details tab
        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text="📋 Playlist Details")
        
        # Details text widget
        details_text_frame = ttk.Frame(details_frame)
        details_text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.details_text = tk.Text(details_text_frame, wrap="word", height=20, state="disabled")
        details_scrollbar = ttk.Scrollbar(details_text_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
    
    def _create_predefined_playlists(self) -> None:
        """Create predefined smart playlists if they don't exist."""
        existing_playlists = {p['name'] for p in self.smart_playlist_manager.get_all_smart_playlists()}
        
        for playlist in PREDEFINED_PLAYLISTS:
            if playlist.name not in existing_playlists:
                try:
                    self.smart_playlist_manager.create_smart_playlist(playlist)
                except Exception as e:
                    print(f"Error creating predefined playlist '{playlist.name}': {e}")
        
        self._load_smart_playlists()
    
    def _load_smart_playlists(self) -> None:
        """Load smart playlists into the treeview."""
        # Clear existing items
        for item in self.playlist_tree.get_children():
            self.playlist_tree.delete(item)
        
        self.playlists = self.smart_playlist_manager.get_all_smart_playlists()
        
        for playlist in self.playlists:
            # Format updated date
            updated = playlist.get('updated_at', '')
            if updated:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    updated = dt.strftime('%m/%d')
                except:
                    updated = updated[:10] if len(updated) > 10 else updated
            
            # Get track count by generating playlist (cached or quick count)
            try:
                track_count = len(self.smart_playlist_manager.generate_playlist_tracks(playlist['id']))
            except:
                track_count = "?"
            
            # Insert into tree
            item_id = self.playlist_tree.insert("", "end", 
                text=playlist['name'],
                values=(
                    playlist.get('rule_count', 0),
                    track_count,
                    updated
                ),
                tags=(playlist['id'],)
            )
            
            # Add description as a child if available
            if playlist.get('description'):
                self.playlist_tree.insert(item_id, "end", 
                    text=f"📝 {playlist['description']}", 
                    values=("", "", "")
                )
    
    def _on_search_change(self, *args) -> None:
        """Handle search/filter changes."""
        search_term = self.search_var.get().lower()
        
        # Show/hide items based on search
        for item in self.playlist_tree.get_children():
            playlist_name = self.playlist_tree.item(item, 'text').lower()
            if search_term in playlist_name:
                self.playlist_tree.item(item, tags=self.playlist_tree.item(item, 'tags'))
            else:
                # Hide item (simplified approach)
                pass
    
    def _on_playlist_select(self, _event) -> None:
        """Handle playlist selection."""
        selection = self.playlist_tree.selection()
        if selection:
            item = selection[0]
            tags = self.playlist_tree.item(item, 'tags')
            
            if tags and tags[0]:  # Has playlist ID
                self.generate_button.config(state="normal")
                self.delete_button.config(state="normal")
                self._update_playlist_details(int(tags[0]))
                self._update_stats(int(tags[0]))
            else:
                self.generate_button.config(state="disabled")
                self.delete_button.config(state="disabled")
        else:
            self.generate_button.config(state="disabled")
            self.delete_button.config(state="disabled")
    
    def _update_playlist_details(self, playlist_id: int) -> None:
        """Update the playlist details view."""
        try:
            # Get playlist info
            playlist_info = None
            for p in self.playlists:
                if p['id'] == playlist_id:
                    playlist_info = p
                    break
            
            if not playlist_info:
                return
            
            # Get rules
            rules = self.smart_playlist_manager.get_playlist_rules(playlist_id)
            
            # Build details text
            details = []
            details.append(f"📋 Playlist: {playlist_info['name']}")
            details.append(f"📝 Description: {playlist_info.get('description', 'No description')}")
            details.append(f"📅 Created: {playlist_info.get('created_at', 'Unknown')}")
            details.append(f"🔄 Updated: {playlist_info.get('updated_at', 'Unknown')}")
            details.append(f"🎵 Limit: {playlist_info.get('limit_count', 'No limit')}")
            details.append(f"📊 Order: {playlist_info.get('order_by', 'Default')} {'(DESC)' if playlist_info.get('order_desc') else '(ASC)'}")
            details.append(f"🔗 Logic: {'Match ALL rules (AND)' if playlist_info.get('match_all') else 'Match ANY rule (OR)'}")
            details.append("")
            details.append("📋 RULES:")
            details.append("-" * 40)
            
            for i, rule in enumerate(rules, 1):
                logical = f" {rule['logical_operator'].upper()} " if i > 1 else ""
                value2_text = f" and {rule['value2']}" if rule['value2'] else ""
                details.append(f"{i}. {logical}{rule['criteria']} {rule['operator']} {rule['value']}{value2_text}")
            
            # Update text widget
            self.details_text.config(state="normal")
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, "\n".join(details))
            self.details_text.config(state="disabled")
            
        except Exception as e:
            self.details_text.config(state="normal")
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, f"Error loading details: {e}")
            self.details_text.config(state="disabled")
    
    def _update_stats(self, playlist_id: int) -> None:
        """Update statistics for the selected playlist."""
        try:
            tracks = self.smart_playlist_manager.generate_playlist_tracks(playlist_id)
            total_tracks = len(tracks)
            
            if total_tracks > 0:
                total_duration = sum(track.get('duration', 0) for track in tracks)
                avg_bpm = sum(track.get('bpm', 0) for track in tracks if track.get('bpm', 0) > 0) / max(1, len([t for t in tracks if t.get('bpm', 0) > 0]))
                
                # Format duration
                hours = int(total_duration // 3600)
                minutes = int((total_duration % 3600) // 60)
                
                stats_text = f"📊 {total_tracks} tracks • {hours}h {minutes}m • Avg BPM: {avg_bpm:.0f}"
            else:
                stats_text = "📊 No tracks match the criteria"
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.stats_label.config(text=f"📊 Error: {e}")
    
    def _on_playlist_double_click(self, _event) -> None:
        """Handle double-click on playlist."""
        self._generate_selected_playlist()
    
    def _on_playlist_right_click(self, event) -> None:
        """Handle right-click on playlist."""
        # Create context menu
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="🎵 Generate Playlist", command=self._generate_selected_playlist)
        context_menu.add_separator()
        context_menu.add_command(label="✏️ Edit Playlist", command=self._edit_selected_playlist)
        context_menu.add_command(label="📋 Duplicate Playlist", command=self._duplicate_selected_playlist)
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ Delete Playlist", command=self._delete_selected_playlist)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _generate_selected_playlist(self) -> None:
        """Generate tracks for the selected playlist."""
        selection = self.playlist_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.playlist_tree.item(item, 'tags')
        
        if not tags or not tags[0]:
            return
        
        playlist_id = int(tags[0])
        
        try:
            tracks = self.smart_playlist_manager.generate_playlist_tracks(playlist_id)
            self._display_tracks(tracks)
            self._update_stats(playlist_id)
        except Exception as e:
            messagebox.showerror("Error", f"Error generating playlist: {e}")
    
    def _display_tracks(self, tracks: List[Dict[str, Any]]) -> None:
        """Display tracks in the treeview with enhanced information."""
        # Clear existing tracks
        for item in self.tracks_tree.get_children():
            self.tracks_tree.delete(item)
        
        # Add new tracks
        for track in tracks:
            # Format duration
            duration = track.get('duration', 0)
            duration_str = f"{int(duration//60)}:{int(duration%60):02d}" if duration else "N/A"
            
            self.tracks_tree.insert("", "end", values=(
                track.get('artist', 'Unknown'),
                track.get('title', 'Unknown'),
                track.get('album', 'Unknown'),
                track.get('genre', 'Unknown'),
                track.get('year', 'N/A'),
                track.get('bpm', 'N/A'),
                duration_str,
                track.get('play_count', 0)
            ), tags=(track.get('file_path', ''),))
    
    def _on_track_double_click(self, _event) -> None:
        """Handle double-click on track."""
        self._play_selected_track()
    
    def _on_track_right_click(self, event) -> None:
        """Handle right-click on track."""
        # Create context menu for tracks
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="▶️ Play Track", command=self._play_selected_track)
        context_menu.add_separator()
        context_menu.add_command(label="📋 Copy Path", command=self._copy_track_path)
        context_menu.add_command(label="📁 Show in Finder", command=self._show_track_in_finder)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _play_selected_track(self) -> None:
        """Play the selected track."""
        selection = self.tracks_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.tracks_tree.item(item, 'tags')
        if tags and tags[0]:
            file_path = tags[0]
            self.play_track_callback(file_path)
            
            # Record playback
            self.smart_playlist_manager.record_playback(file_path)
    
    def _copy_track_path(self) -> None:
        """Copy track path to clipboard."""
        selection = self.tracks_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.tracks_tree.item(item, 'tags')
        if tags and tags[0]:
            self.clipboard_clear()
            self.clipboard_append(tags[0])
    
    def _show_track_in_finder(self) -> None:
        """Show track in system file manager."""
        selection = self.tracks_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.tracks_tree.item(item, 'tags')
        if tags and tags[0]:
            import subprocess
            import os
            file_path = tags[0]
            
            try:
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', '/select,', file_path])
                elif os.name == 'posix':  # macOS/Linux
                    subprocess.run(['open', '-R', file_path])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file location: {e}")
    
    def _create_quick_playlist(self) -> None:
        """Open dialog to create a quick smart playlist."""
        dialog = SimpleSmartPlaylistDialog(self, self.smart_playlist_manager)
        if dialog.result:
            self._load_smart_playlists()
    
    def _create_advanced_playlist(self) -> None:
        """Open dialog to create an advanced smart playlist."""
        dialog = AdvancedSmartPlaylistDialog(self, self.smart_playlist_manager)
        if dialog.result:
            self._load_smart_playlists()
    
    def _edit_selected_playlist(self) -> None:
        """Edit the selected playlist."""
        # TODO: Implement playlist editing
        messagebox.showinfo("Coming Soon", "Playlist editing will be available in a future update.")
    
    def _duplicate_selected_playlist(self) -> None:
        """Duplicate the selected playlist."""
        # TODO: Implement playlist duplication
        messagebox.showinfo("Coming Soon", "Playlist duplication will be available in a future update.")
    
    def _delete_selected_playlist(self) -> None:
        """Delete the selected playlist."""
        selection = self.playlist_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.playlist_tree.item(item, 'tags')
        
        if not tags or not tags[0]:
            return
        
        playlist_id = int(tags[0])
        playlist_name = self.playlist_tree.item(item, 'text')
        
        if messagebox.askyesno("Confirm Delete", f"Delete playlist '{playlist_name}'?"):
            try:
                self.smart_playlist_manager.delete_smart_playlist(playlist_id)
                self._load_smart_playlists()
                # Clear tracks display
                for item in self.tracks_tree.get_children():
                    self.tracks_tree.delete(item)
                self.stats_label.config(text="No playlist selected")
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting playlist: {e}")
    
    def _export_playlist(self) -> None:
        """Export the current playlist to a file."""
        tracks = []
        for item in self.tracks_tree.get_children():
            values = self.tracks_tree.item(item, 'values')
            tags = self.tracks_tree.item(item, 'tags')
            if tags and tags[0]:
                tracks.append({
                    'file_path': tags[0],
                    'artist': values[0],
                    'title': values[1],
                    'album': values[2],
                    'genre': values[3],
                    'year': values[4],
                    'bpm': values[5],
                    'duration': values[6]
                })
        
        if not tracks:
            messagebox.showwarning("Warning", "No tracks to export.")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".m3u",
            filetypes=[("M3U Playlist", "*.m3u"), ("Text File", "*.txt"), ("All Files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    if filename.endswith('.m3u'):
                        f.write("#EXTM3U\n")
                        for track in tracks:
                            f.write(f"#EXTINF:-1,{track['artist']} - {track['title']}\n")
                            f.write(f"{track['file_path']}\n")
                    else:
                        for track in tracks:
                            f.write(f"{track['file_path']}\n")
                
                messagebox.showinfo("Success", f"Playlist exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exporting playlist: {e}")
    
    def _refresh_current_playlist(self) -> None:
        """Refresh the currently displayed playlist."""
        selection = self.playlist_tree.selection()
        if selection:
            self._generate_selected_playlist()


# Backward compatibility - keep the old dialog class name
SmartPlaylistDialog = SimpleSmartPlaylistDialog