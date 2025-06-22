# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Standard Workflow

1. First think through the problem, read the codebase for relevant files, and write a plan to projectplan.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the projectplan.md file with a summary of the changes you made and any other relevant information.

## Commands

### Setup and Installation
```bash
# Setup virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Setup configuration
cp .env.example .env  # Edit with your API credentials
```

### Running the Application
```bash
# Run main DJ library application
python main.py

# Run specific prototypes (multiple variants available)
python serato_pro_style.py
python cuepoint_desktop_real.py
python djlibraryalfin_complete.py
```

### Testing
```bash
# Run all tests
python run_tests.py

# Run specific test files directly
python test_sorting_complete.py
python test_visual_system.py
python test_sentry_integration.py
```

### Validation and Debugging
```bash
# Validate specific components
python validate_tracklistview.py
python validate_sliding_panels.py
python comprehensive_validation.py

# Debug specific functionality  
python debug_double_click.py
python debug_real_app.py
```

## Architecture Overview

DjAlfin is a professional DJ library management application built with PySide6/Qt6. The architecture follows a layered approach with clear separation of concerns:

### Core Architecture Layers

**Presentation Layer (`ui/`)**
- `MainWindow`: Central application window with modern sliding panel system
- `TrackListView`: Enhanced table view with professional DJ features (sorting, column management)
- Sliding Panels: Modern overlay system replacing traditional fixed panels
  - `PlaylistSlidingPanel`: Playlist management with drag & drop
  - `MetadataSlidingPanel`: Track metadata editing with real BPM analysis
- `PlaybackPanel`: Minimal audio controls with volume and navigation

**Service Layer (`services/`)**
- `PlaylistService`: High-level playlist operations with caching (5-min TTL)
- `BPMService`: Wrapper for BPM analysis operations
- `MetadataService`: Metadata enrichment and management

**Core Business Logic (`core/`)**
- `AudioService`: Qt-based audio playback using QMediaPlayer/QAudioOutput
- `BPMAnalyzer`: Professional BPM detection using librosa with multiple algorithms
- `LibraryScanner`: Audio file discovery and metadata extraction
- `SmartPlaylistEngine`: Rule-based playlist generation
- `MetadataEnricher`: Integration with Spotify, Discogs, Last.fm, MusicBrainz

**Data Layer (`core/database.py`)**
- SQLite database with automatic migrations
- Tables: tracks, smart_playlists, playlist_rules, playlists, playlist_tracks
- Supports genre normalization and BPM storage

### Key Design Patterns

**Modern UI Architecture**
- Sliding panels replace traditional fixed panels for better space utilization
- Edge hover areas (15px trigger zones) for panel activation
- Signal/slot communication between components
- Enhanced table model with lazy loading and caching

**Audio Analysis Pipeline**
- Real librosa-based BPM analysis (replaces fake random values)
- Multi-algorithm tempo detection with confidence scoring
- Thread-based processing to prevent UI blocking
- Database integration for storing analysis results

**Metadata Enrichment System**
- Service-oriented architecture for external API integration
- Genre normalization with blacklist filtering ("and", "chart", "top", "hits")
- Batch operations for library-wide updates
- Error handling and fallback mechanisms

**Smart Playlist Engine**
- Rule-based filtering (artist, genre, BPM, year, play_count, etc.)
- Boolean logic support (AND/OR operations)
- Real-time updates when track metadata changes
- Export/import support (M3U, PLS, JSON formats)

### Database Schema

The application uses SQLite with the following key tables:
- `tracks`: Core track storage (title, artist, album, bpm, key, genre, file_path, etc.)
- `smart_playlists`: Playlist definitions with rules and match criteria
- `playlists`: Regular playlist storage
- `playlist_tracks`: Track-to-playlist associations

### Critical Components

**BPM Analysis System** (`core/bmp_analyzer.py`)
- Uses librosa for professional-grade tempo detection
- Multiple algorithm validation (primary/secondary analysis)
- Half/double tempo detection and correction
- Beat tracking and rhythm analysis
- Confidence scoring (0.0-1.0)

**Sliding Panel System** (`ui/components/`)
- Modern overlay-based UI replacing fixed panels
- Edge hover detection for seamless activation
- Drag & drop support for playlist management
- Real-time metadata editing with database integration

**Enhanced Track Model** (`ui/base/enhanced_track_model.py`)
- Qt model/view architecture for high-performance track display
- Lazy loading for large libraries
- Advanced sorting with numerical/text type awareness
- Column management with user preferences

### Development Notes

- All components use Qt6 signal/slot architecture for loose coupling
- Database operations are wrapped in services with caching
- BPM analysis runs in background threads to maintain UI responsiveness  
- Error handling includes Sentry integration for production monitoring
- Configuration management through `config/secure_config.py`
- Comprehensive logging system in `core/logging_config.py`

The codebase prioritizes simplicity and maintainability, with each component having a single responsibility and clear interfaces between layers.