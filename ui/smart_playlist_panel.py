"""
Smart Playlist Panel for DjAlfin
UI component for creating and managing smart playlists.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Dict, Any
from core.smart_playlist_manager import (
    SmartPlaylistManager, SmartPlaylist, PlaylistRule, 
    PlaylistCriteria, ComparisonOperator, PREDEFINED_PLAYLISTS
)


class SmartPlaylistPanel(ttk.Frame):
    """Panel for managing smart playlists."""
    
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
        # Title
        title_label = ttk.Label(self, text="Smart Playlists", font=("Helvetica", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Playlist list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)
        
        # Scrollable listbox for playlists
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.playlist_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            selectmode="single",
            height=8
        )
        self.playlist_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.playlist_listbox.yview)
        
        # Bind selection event
        self.playlist_listbox.bind("<<ListboxSelect>>", self._on_playlist_select)
        self.playlist_listbox.bind("<Double-Button-1>", self._on_playlist_double_click)
        
        # Buttons frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=(10, 0))
        
        self.generate_button = ttk.Button(
            button_frame, 
            text="Generate Playlist", 
            command=self._generate_selected_playlist,
            state="disabled"
        )
        self.generate_button.pack(side="left", padx=(0, 5))
        
        self.create_button = ttk.Button(
            button_frame, 
            text="Create New", 
            command=self._create_new_playlist
        )
        self.create_button.pack(side="left", padx=5)
        
        self.delete_button = ttk.Button(
            button_frame, 
            text="Delete", 
            command=self._delete_selected_playlist,
            state="disabled"
        )
        self.delete_button.pack(side="left", padx=5)
        
        # Generated tracks frame
        tracks_frame = ttk.LabelFrame(self, text="Generated Tracks")
        tracks_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Tracks treeview
        self.tracks_tree = ttk.Treeview(
            tracks_frame,
            columns=("artist", "title", "genre", "bpm"),
            show="headings",
            height=6
        )
        
        # Configure columns
        self.tracks_tree.heading("artist", text="Artist")
        self.tracks_tree.heading("title", text="Title")
        self.tracks_tree.heading("genre", text="Genre")
        self.tracks_tree.heading("bpm", text="BPM")
        
        self.tracks_tree.column("artist", width=120)
        self.tracks_tree.column("title", width=150)
        self.tracks_tree.column("genre", width=80)
        self.tracks_tree.column("bpm", width=60)
        
        # Tracks scrollbar
        tracks_scrollbar = ttk.Scrollbar(tracks_frame, orient="vertical", command=self.tracks_tree.yview)
        self.tracks_tree.configure(yscrollcommand=tracks_scrollbar.set)
        
        self.tracks_tree.pack(side="left", fill="both", expand=True)
        tracks_scrollbar.pack(side="right", fill="y")
        
        # Bind double-click to play track
        self.tracks_tree.bind("<Double-Button-1>", self._on_track_double_click)
    
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
        """Load smart playlists into the listbox."""
        self.playlist_listbox.delete(0, tk.END)
        self.playlists = self.smart_playlist_manager.get_all_smart_playlists()
        
        for playlist in self.playlists:
            self.playlist_listbox.insert(tk.END, playlist['name'])
    
    def _on_playlist_select(self, _event) -> None:
        """Handle playlist selection."""
        selection = self.playlist_listbox.curselection()
        if selection:
            self.generate_button.config(state="normal")
            self.delete_button.config(state="normal")
        else:
            self.generate_button.config(state="disabled")
            self.delete_button.config(state="disabled")
    
    def _on_playlist_double_click(self, _event) -> None:
        """Handle double-click on playlist."""
        self._generate_selected_playlist()
    
    def _generate_selected_playlist(self) -> None:
        """Generate tracks for the selected playlist."""
        selection = self.playlist_listbox.curselection()
        if not selection:
            return
        
        playlist_index = selection[0]
        playlist = self.playlists[playlist_index]
        
        try:
            tracks = self.smart_playlist_manager.generate_playlist_tracks(playlist['id'])
            self._display_tracks(tracks)
        except Exception as e:
            messagebox.showerror("Error", f"Error generating playlist: {e}")
    
    def _display_tracks(self, tracks: List[Dict[str, Any]]) -> None:
        """Display tracks in the treeview."""
        # Clear existing tracks
        for item in self.tracks_tree.get_children():
            self.tracks_tree.delete(item)
        
        # Add new tracks
        for track in tracks:
            self.tracks_tree.insert("", "end", values=(
                track.get('artist', 'Unknown'),
                track.get('title', 'Unknown'),
                track.get('genre', 'Unknown'),
                track.get('bpm', 'N/A')
            ), tags=(track.get('file_path', ''),))
    
    def _on_track_double_click(self, _event) -> None:
        """Handle double-click on track."""
        selection = self.tracks_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.tracks_tree.item(item, 'tags')
        if tags and tags[0]:
            file_path = tags[0]
            self.play_track_callback(file_path)
    
    def _create_new_playlist(self) -> None:
        """Open dialog to create a new smart playlist."""
        dialog = SmartPlaylistDialog(self, self.smart_playlist_manager)
        if dialog.result:
            self._load_smart_playlists()
    
    def _delete_selected_playlist(self) -> None:
        """Delete the selected playlist."""
        selection = self.playlist_listbox.curselection()
        if not selection:
            return
        
        playlist_index = selection[0]
        playlist = self.playlists[playlist_index]
        
        if messagebox.askyesno("Confirm Delete", f"Delete playlist '{playlist['name']}'?"):
            try:
                self.smart_playlist_manager.delete_smart_playlist(playlist['id'])
                self._load_smart_playlists()
                # Clear tracks display
                for item in self.tracks_tree.get_children():
                    self.tracks_tree.delete(item)
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting playlist: {e}")


class SmartPlaylistDialog:
    """Dialog for creating new smart playlists."""
    
    def __init__(self, parent, smart_playlist_manager: SmartPlaylistManager):
        self.parent = parent
        self.smart_playlist_manager = smart_playlist_manager
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Smart Playlist")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self.dialog.wait_window()
    
    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        # Name
        ttk.Label(self.dialog, text="Playlist Name:").pack(pady=5)
        self.name_entry = ttk.Entry(self.dialog, width=40)
        self.name_entry.pack(pady=5)
        
        # Simple rule for now - just genre
        ttk.Label(self.dialog, text="Genre Contains:").pack(pady=5)
        self.genre_entry = ttk.Entry(self.dialog, width=40)
        self.genre_entry.pack(pady=5)
        
        # Limit
        ttk.Label(self.dialog, text="Limit (optional):").pack(pady=5)
        self.limit_entry = ttk.Entry(self.dialog, width=40)
        self.limit_entry.pack(pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Create", command=self._create_playlist).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side="left", padx=5)
    
    def _create_playlist(self) -> None:
        """Create the playlist."""
        name = self.name_entry.get().strip()
        genre = self.genre_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Please enter a playlist name.")
            return
        
        rules = []
        if genre:
            rules.append(PlaylistRule(
                PlaylistCriteria.GENRE, 
                ComparisonOperator.CONTAINS, 
                genre
            ))
        
        limit = None
        if self.limit_entry.get().strip():
            try:
                limit = int(self.limit_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Limit must be a number.")
                return
        
        playlist = SmartPlaylist(name=name, rules=rules, limit=limit)
        
        try:
            self.smart_playlist_manager.create_smart_playlist(playlist)
            self.result = True
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error creating playlist: {e}")