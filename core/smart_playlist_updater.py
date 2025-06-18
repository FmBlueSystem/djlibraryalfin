import time
import os
import json
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import List, Set

from core.database import get_db_path, create_connection
from core.smart_playlist_engine import SmartPlaylistEngine

class SmartPlaylistUpdater(FileSystemEventHandler):
    """
    Manejador de eventos del sistema de archivos para actualizar
    listas de reproducción inteligentes cuando cambian los archivos de música.
    """
    def __init__(self, db_path: str, music_folders: List[str]):
        super().__init__()
        self.db_path = db_path
        self.music_folders = music_folders
        self.engine = SmartPlaylistEngine(db_path)
        self.affected_playlists: Set[int] = set()
        print(f"Smart Playlist Updater inicializado para las carpetas: {music_folders}")

    def on_modified(self, event):
        self._handle_event(event)

    def on_created(self, event):
        self._handle_event(event)

    def on_deleted(self, event):
        self._handle_event(event)
    
    def _handle_event(self, event):
        """Filtra eventos para actuar solo sobre archivos de audio."""
        if event.is_directory:
            return
        
        # Extensiones de archivo de audio comunes
        audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']
        file_path = event.src_path
        
        if any(file_path.lower().endswith(ext) for ext in audio_extensions):
            print(f"Detectado cambio en el archivo de audio: {file_path}")
            # En un escenario real y complejo, se podría analizar qué cambió
            # y solo actualizar las playlists afectadas.
            # Por simplicidad, aquí actualizaremos todas las playlists dinámicas.
            self.update_all_dynamic_playlists()

    def update_all_dynamic_playlists(self):
        """
        Recalcula todas las listas de reproducción que no están congeladas.
        """
        conn = create_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            # Obtener todas las playlists dinámicas
            cursor.execute("SELECT id, rules, match_all FROM smart_playlists WHERE is_static = 0")
            playlists_to_update = cursor.fetchall()
            
            print(f"Encontradas {len(playlists_to_update)} playlists dinámicas para actualizar.")
            
            for pl in playlists_to_update:
                playlist_id = pl['id']
                rules = json.loads(pl['rules'])
                match_all = bool(pl['match_all'])
                
                # Obtener los nuevos IDs de pista
                new_track_ids = self.engine.get_tracks_for_rules(rules, match_all)
                
                # Obtener los IDs de pista actuales para comparar
                cursor.execute("SELECT track_id FROM smart_playlist_tracks WHERE playlist_id = ?", (playlist_id,))
                current_track_ids = {row['track_id'] for row in cursor.fetchall()}

                # Si no hay cambios, no hacer nada
                if set(new_track_ids) == current_track_ids:
                    print(f"Playlist {playlist_id}: Sin cambios.")
                    continue

                print(f"Playlist {playlist_id}: Actualizando pistas...")
                # Borrar las pistas antiguas
                cursor.execute("DELETE FROM smart_playlist_tracks WHERE playlist_id = ?", (playlist_id,))
                
                # Insertar las nuevas pistas
                if new_track_ids:
                    new_tracks_data = [(playlist_id, track_id) for track_id in new_track_ids]
                    cursor.executemany("INSERT INTO smart_playlist_tracks (playlist_id, track_id) VALUES (?, ?)", new_tracks_data)
            
            conn.commit()
            print("Actualización de playlists dinámicas completada.")

        except Exception as e:
            print(f"Error al actualizar las playlists dinámicas: {e}")
        finally:
            if conn:
                conn.close()


def start_playlist_updater_thread(music_folders: List[str]):
    """
    Inicia el observador del sistema de archivos en un hilo separado.
    """
    db_path = get_db_path()
    event_handler = SmartPlaylistUpdater(db_path, music_folders)
    observer = Observer()
    
    for folder in music_folders:
        if os.path.exists(folder):
            observer.schedule(event_handler, folder, recursive=True)
            print(f"Observador configurado para la carpeta: {folder}")
        else:
            print(f"Advertencia: La carpeta de música no existe, no se puede observar: {folder}")
            
    if not observer.emitters:
        print("Error: No hay carpetas válidas para observar. El actualizador no se iniciará.")
        return None

    observer.start()
    print("El hilo del observador de playlists ha comenzado.")
    return observer

# Ejemplo de uso
if __name__ == '__main__':
    # Simular la configuración de la aplicación
    # Reemplazar con las carpetas de música reales del usuario
    user_music_folders = [os.path.expanduser("~/Music")] 
    
    observer = start_playlist_updater_thread(user_music_folders)
    
    if observer:
        try:
            while True:
                time.sleep(5)
                print("...") # Mantener el hilo principal vivo para la demostración
        except KeyboardInterrupt:
            observer.stop()
            print("El observador se ha detenido.")
        observer.join() 