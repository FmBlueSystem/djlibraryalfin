"""
Advanced Smart Playlist Dialog for DjAlfin
Enhanced UI component for creating complex smart playlists with multiple criteria.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
from core.smart_playlist_manager import (
    SmartPlaylistManager, SmartPlaylist, PlaylistRule, 
    PlaylistCriteria, ComparisonOperator, LogicalOperator
)


class AdvancedSmartPlaylistDialog:
    """Advanced dialog for creating smart playlists with multiple criteria."""
    
    def __init__(self, parent, smart_playlist_manager: SmartPlaylistManager):
        self.parent = parent
        self.smart_playlist_manager = smart_playlist_manager
        self.result = None
        self.rules = []
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Advanced Smart Playlist")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self._create_widgets()
        self._add_initial_rule()
        self.dialog.wait_window()
    
    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        # Main container with scrollbar
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Playlist info section
        info_frame = ttk.LabelFrame(main_frame, text="Playlist Information", padding=10)
        info_frame.pack(fill="x", pady=(0, 10))
        
        # Name
        ttk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.name_entry = ttk.Entry(info_frame, width=40)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        # Description
        ttk.Label(info_frame, text="Description:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.description_entry = ttk.Entry(info_frame, width=40)
        self.description_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(5, 0))
        
        info_frame.columnconfigure(1, weight=1)
        
        # Rules section
        rules_frame = ttk.LabelFrame(main_frame, text="Playlist Rules", padding=10)
        rules_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Rules container with scrollbar
        rules_canvas = tk.Canvas(rules_frame, height=200)
        rules_scrollbar = ttk.Scrollbar(rules_frame, orient="vertical", command=rules_canvas.yview)
        self.rules_container = ttk.Frame(rules_canvas)
        
        rules_canvas.configure(yscrollcommand=rules_scrollbar.set)
        rules_canvas.pack(side="left", fill="both", expand=True)
        rules_scrollbar.pack(side="right", fill="y")
        
        rules_canvas.create_window((0, 0), window=self.rules_container, anchor="nw")
        self.rules_container.bind("<Configure>", lambda e: rules_canvas.configure(scrollregion=rules_canvas.bbox("all")))
        
        # Add/Remove rule buttons
        rule_buttons_frame = ttk.Frame(rules_frame)
        rule_buttons_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(rule_buttons_frame, text="+ Add Rule", command=self._add_rule).pack(side="left", padx=(0, 5))
        ttk.Button(rule_buttons_frame, text="- Remove Last", command=self._remove_last_rule).pack(side="left")
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="Playlist Options", padding=10)
        options_frame.pack(fill="x", pady=(0, 10))
        
        # Match logic
        ttk.Label(options_frame, text="Match:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.match_var = tk.StringVar(value="all")
        match_frame = ttk.Frame(options_frame)
        match_frame.grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(match_frame, text="All rules (AND)", variable=self.match_var, value="all").pack(side="left")
        ttk.Radiobutton(match_frame, text="Any rule (OR)", variable=self.match_var, value="any").pack(side="left", padx=(10, 0))
        
        # Limit
        ttk.Label(options_frame, text="Limit:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        limit_frame = ttk.Frame(options_frame)
        limit_frame.grid(row=1, column=1, sticky="w", pady=(5, 0))
        self.limit_entry = ttk.Entry(limit_frame, width=10)
        self.limit_entry.pack(side="left")
        ttk.Label(limit_frame, text="tracks (leave empty for no limit)").pack(side="left", padx=(5, 0))
        
        # Order by
        ttk.Label(options_frame, text="Order by:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        order_frame = ttk.Frame(options_frame)
        order_frame.grid(row=2, column=1, sticky="w", pady=(5, 0))
        
        self.order_by_var = tk.StringVar()
        order_combo = ttk.Combobox(order_frame, textvariable=self.order_by_var, width=15, state="readonly")
        order_combo['values'] = ('', 'title', 'artist', 'album', 'genre', 'year', 'bpm', 'duration', 'play_count')
        order_combo.pack(side="left")
        
        self.order_desc_var = tk.BooleanVar()
        ttk.Checkbutton(order_frame, text="Descending", variable=self.order_desc_var).pack(side="left", padx=(10, 0))
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Preview (first 10 tracks)", padding=10)
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Preview treeview
        self.preview_tree = ttk.Treeview(
            preview_frame,
            columns=("artist", "title", "genre", "year"),
            show="headings",
            height=6
        )
        
        self.preview_tree.heading("artist", text="Artist")
        self.preview_tree.heading("title", text="Title")
        self.preview_tree.heading("genre", text="Genre")
        self.preview_tree.heading("year", text="Year")
        
        self.preview_tree.column("artist", width=120)
        self.preview_tree.column("title", width=150)
        self.preview_tree.column("genre", width=80)
        self.preview_tree.column("year", width=60)
        
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_tree.pack(side="left", fill="both", expand=True)
        preview_scrollbar.pack(side="right", fill="y")
        
        # Preview button
        ttk.Button(preview_frame, text="🔍 Update Preview", command=self._update_preview).pack(pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Create Playlist", command=self._create_playlist).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side="right")
    
    def _add_initial_rule(self) -> None:
        """Add the first rule."""
        self._add_rule()
    
    def _add_rule(self) -> None:
        """Add a new rule widget."""
        rule_frame = ttk.Frame(self.rules_container)
        rule_frame.pack(fill="x", pady=2)
        
        rule_index = len(self.rules)
        
        # Logical operator (skip for first rule)
        if rule_index > 0:
            logical_var = tk.StringVar(value="and")
            logical_combo = ttk.Combobox(rule_frame, textvariable=logical_var, width=8, state="readonly")
            logical_combo['values'] = ('and', 'or')
            logical_combo.pack(side="left", padx=(0, 5))
        else:
            logical_var = tk.StringVar(value="and")
            logical_combo = None
        
        # Criteria
        criteria_var = tk.StringVar()
        criteria_combo = ttk.Combobox(rule_frame, textvariable=criteria_var, width=15, state="readonly")
        criteria_combo['values'] = (
            'genre', 'artist', 'album', 'title', 'year', 'bpm', 'duration',
            'recently_played', 'most_played', 'never_played', 'play_count'
        )
        criteria_combo.pack(side="left", padx=(0, 5))
        criteria_combo.bind('<<ComboboxSelected>>', lambda e, idx=rule_index: self._on_criteria_change(idx))
        
        # Operator
        operator_var = tk.StringVar()
        operator_combo = ttk.Combobox(rule_frame, textvariable=operator_var, width=12, state="readonly")
        operator_combo.pack(side="left", padx=(0, 5))
        
        # Value 1
        value1_var = tk.StringVar()
        value1_entry = ttk.Entry(rule_frame, textvariable=value1_var, width=15)
        value1_entry.pack(side="left", padx=(0, 5))
        
        # Value 2 (for BETWEEN operator)
        value2_var = tk.StringVar()
        value2_entry = ttk.Entry(rule_frame, textvariable=value2_var, width=15)
        value2_entry.pack(side="left", padx=(0, 5))
        value2_entry.pack_forget()  # Hidden by default
        
        # Remove button
        remove_btn = ttk.Button(rule_frame, text="×", width=3, 
                               command=lambda idx=rule_index: self._remove_rule(idx))
        remove_btn.pack(side="right")
        
        # Store rule widgets
        rule_widgets = {
            'frame': rule_frame,
            'logical_combo': logical_combo,
            'logical_var': logical_var,
            'criteria_combo': criteria_combo,
            'criteria_var': criteria_var,
            'operator_combo': operator_combo,
            'operator_var': operator_var,
            'value1_entry': value1_entry,
            'value1_var': value1_var,
            'value2_entry': value2_entry,
            'value2_var': value2_var,
            'remove_btn': remove_btn
        }
        
        self.rules.append(rule_widgets)
        
        # Set default values
        criteria_combo.set('genre')
        self._on_criteria_change(rule_index)
    
    def _on_criteria_change(self, rule_index: int) -> None:
        """Handle criteria change to update available operators."""
        if rule_index >= len(self.rules):
            return
            
        rule = self.rules[rule_index]
        criteria = rule['criteria_var'].get()
        
        # Update operators based on criteria
        if criteria in ['genre', 'artist', 'album', 'title']:
            operators = ['equals', 'contains', 'starts_with', 'ends_with', 'not_equals', 'not_contains']
        elif criteria in ['year', 'bpm', 'duration', 'play_count']:
            operators = ['equals', 'greater_than', 'less_than', 'between']
        elif criteria in ['recently_played', 'most_played']:
            operators = ['in_last_days']
        elif criteria == 'never_played':
            operators = ['equals']
        else:
            operators = ['equals']
        
        rule['operator_combo']['values'] = operators
        if operators:
            rule['operator_var'].set(operators[0])
            self._on_operator_change(rule_index)
    
    def _on_operator_change(self, rule_index: int) -> None:
        """Handle operator change to show/hide second value field."""
        if rule_index >= len(self.rules):
            return
            
        rule = self.rules[rule_index]
        operator = rule['operator_var'].get()
        
        if operator == 'between':
            rule['value2_entry'].pack(side="left", padx=(0, 5), before=rule['remove_btn'])
        else:
            rule['value2_entry'].pack_forget()
    
    def _remove_rule(self, rule_index: int) -> None:
        """Remove a specific rule."""
        if rule_index < len(self.rules) and len(self.rules) > 1:
            rule = self.rules.pop(rule_index)
            rule['frame'].destroy()
            
            # Update rule indices for remaining rules
            for i, remaining_rule in enumerate(self.rules):
                remaining_rule['remove_btn'].configure(
                    command=lambda idx=i: self._remove_rule(idx)
                )
    
    def _remove_last_rule(self) -> None:
        """Remove the last rule."""
        if len(self.rules) > 1:
            self._remove_rule(len(self.rules) - 1)
    
    def _update_preview(self) -> None:
        """Update the preview with current rules."""
        try:
            rules = self._build_rules()
            if not rules:
                return
            
            preview_tracks = self.smart_playlist_manager.get_playlist_preview(rules, limit=10)
            
            # Clear existing items
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
            
            # Add preview tracks
            for track in preview_tracks:
                self.preview_tree.insert("", "end", values=(
                    track.get('artist', 'Unknown'),
                    track.get('title', 'Unknown'),
                    track.get('genre', 'Unknown'),
                    track.get('year', 'N/A')
                ))
                
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error generating preview: {e}")
    
    def _build_rules(self) -> List[PlaylistRule]:
        """Build PlaylistRule objects from the UI."""
        rules = []
        
        for rule_widgets in self.rules:
            criteria_str = rule_widgets['criteria_var'].get()
            operator_str = rule_widgets['operator_var'].get()
            value1 = rule_widgets['value1_var'].get().strip()
            value2 = rule_widgets['value2_var'].get().strip()
            logical_str = rule_widgets['logical_var'].get()
            
            if not criteria_str or not operator_str or not value1:
                continue
            
            try:
                criteria = PlaylistCriteria(criteria_str)
                operator = ComparisonOperator(operator_str)
                logical = LogicalOperator(logical_str)
                
                rule = PlaylistRule(
                    criteria=criteria,
                    operator=operator,
                    value=value1,
                    value2=value2 if value2 else None,
                    logical_operator=logical
                )
                rules.append(rule)
                
            except ValueError as e:
                messagebox.showerror("Rule Error", f"Invalid rule: {e}")
                return []
        
        return rules
    
    def _create_playlist(self) -> None:
        """Create the playlist."""
        name = self.name_entry.get().strip()
        description = self.description_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Please enter a playlist name.")
            return
        
        rules = self._build_rules()
        if not rules:
            messagebox.showerror("Error", "Please add at least one valid rule.")
            return
        
        # Get options
        match_all = self.match_var.get() == "all"
        
        limit = None
        if self.limit_entry.get().strip():
            try:
                limit = int(self.limit_entry.get().strip())
                if limit <= 0:
                    raise ValueError("Limit must be positive")
            except ValueError:
                messagebox.showerror("Error", "Limit must be a positive number.")
                return
        
        order_by = self.order_by_var.get() if self.order_by_var.get() else None
        order_desc = self.order_desc_var.get()
        
        playlist = SmartPlaylist(
            name=name,
            description=description,
            rules=rules,
            limit=limit,
            order_by=order_by,
            order_desc=order_desc,
            match_all=match_all
        )
        
        try:
            self.smart_playlist_manager.create_smart_playlist(playlist)
            self.result = True
            messagebox.showinfo("Success", f"Smart playlist '{name}' created successfully!")
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error creating playlist: {e}")


# Simple dialog for quick playlist creation (backward compatibility)
class SimpleSmartPlaylistDialog:
    """Simple dialog for quick smart playlist creation."""
    
    def __init__(self, parent, smart_playlist_manager: SmartPlaylistManager):
        self.parent = parent
        self.smart_playlist_manager = smart_playlist_manager
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Quick Smart Playlist")
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
        
        # Quick filters
        ttk.Label(self.dialog, text="Quick Filters:").pack(pady=(15, 5))
        
        # Genre
        genre_frame = ttk.Frame(self.dialog)
        genre_frame.pack(pady=5)
        ttk.Label(genre_frame, text="Genre contains:").pack(side="left")
        self.genre_entry = ttk.Entry(genre_frame, width=20)
        self.genre_entry.pack(side="left", padx=(5, 0))
        
        # BPM range
        bpm_frame = ttk.Frame(self.dialog)
        bpm_frame.pack(pady=5)
        ttk.Label(bpm_frame, text="BPM between:").pack(side="left")
        self.bpm_min_entry = ttk.Entry(bpm_frame, width=8)
        self.bpm_min_entry.pack(side="left", padx=(5, 0))
        ttk.Label(bpm_frame, text="and").pack(side="left", padx=5)
        self.bpm_max_entry = ttk.Entry(bpm_frame, width=8)
        self.bpm_max_entry.pack(side="left")
        
        # Year range
        year_frame = ttk.Frame(self.dialog)
        year_frame.pack(pady=5)
        ttk.Label(year_frame, text="Year from:").pack(side="left")
        self.year_min_entry = ttk.Entry(year_frame, width=8)
        self.year_min_entry.pack(side="left", padx=(5, 0))
        ttk.Label(year_frame, text="to").pack(side="left", padx=5)
        self.year_max_entry = ttk.Entry(year_frame, width=8)
        self.year_max_entry.pack(side="left")
        
        # Limit
        limit_frame = ttk.Frame(self.dialog)
        limit_frame.pack(pady=5)
        ttk.Label(limit_frame, text="Limit to:").pack(side="left")
        self.limit_entry = ttk.Entry(limit_frame, width=8)
        self.limit_entry.pack(side="left", padx=(5, 0))
        ttk.Label(limit_frame, text="tracks").pack(side="left", padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Create", command=self._create_playlist).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Advanced...", command=self._open_advanced).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side="left", padx=5)
    
    def _create_playlist(self) -> None:
        """Create the playlist with simple rules."""
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Please enter a playlist name.")
            return
        
        rules = []
        
        # Add genre rule
        genre = self.genre_entry.get().strip()
        if genre:
            rules.append(PlaylistRule(
                PlaylistCriteria.GENRE, 
                ComparisonOperator.CONTAINS, 
                genre
            ))
        
        # Add BPM rule
        bpm_min = self.bpm_min_entry.get().strip()
        bpm_max = self.bpm_max_entry.get().strip()
        if bpm_min and bpm_max:
            try:
                rules.append(PlaylistRule(
                    PlaylistCriteria.BPM,
                    ComparisonOperator.BETWEEN,
                    float(bpm_min),
                    float(bpm_max)
                ))
            except ValueError:
                messagebox.showerror("Error", "BPM values must be numbers.")
                return
        elif bpm_min:
            try:
                rules.append(PlaylistRule(
                    PlaylistCriteria.BPM,
                    ComparisonOperator.GREATER_THAN,
                    float(bpm_min)
                ))
            except ValueError:
                messagebox.showerror("Error", "BPM value must be a number.")
                return
        
        # Add year rule
        year_min = self.year_min_entry.get().strip()
        year_max = self.year_max_entry.get().strip()
        if year_min and year_max:
            try:
                rules.append(PlaylistRule(
                    PlaylistCriteria.YEAR,
                    ComparisonOperator.BETWEEN,
                    int(year_min),
                    int(year_max)
                ))
            except ValueError:
                messagebox.showerror("Error", "Year values must be numbers.")
                return
        elif year_min:
            try:
                rules.append(PlaylistRule(
                    PlaylistCriteria.YEAR,
                    ComparisonOperator.GREATER_THAN,
                    int(year_min)
                ))
            except ValueError:
                messagebox.showerror("Error", "Year value must be a number.")
                return
        
        # Get limit
        limit = None
        if self.limit_entry.get().strip():
            try:
                limit = int(self.limit_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Limit must be a number.")
                return
        
        if not rules:
            messagebox.showwarning("Warning", "No filters specified. Creating playlist with all tracks.")
        
        playlist = SmartPlaylist(name=name, rules=rules, limit=limit)
        
        try:
            self.smart_playlist_manager.create_smart_playlist(playlist)
            self.result = True
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error creating playlist: {e}")
    
    def _open_advanced(self) -> None:
        """Open the advanced dialog."""
        self.dialog.destroy()
        AdvancedSmartPlaylistDialog(self.parent, self.smart_playlist_manager)