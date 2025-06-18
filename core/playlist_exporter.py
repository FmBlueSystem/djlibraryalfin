import csv
import os
from typing import List, Dict, Any

def _get_track_paths(db_conn, playlist_id: int) -> List[str]:
    """
    Obtiene las rutas de archivo de las pistas de una playlist específica.
    """
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT t.file_path
        FROM tracks t
        JOIN smart_playlist_tracks spt ON t.id = spt.track_id
        WHERE spt.playlist_id = ?
    """, (playlist_id,))
    
    # Usamos abspath para asegurar que las rutas sean absolutas
    return [os.path.abspath(row['file_path']) for row in cursor.fetchall()]

def export_to_m3u(db_conn, playlist_id: int, playlist_name: str, output_dir: str) -> str:
    """
    Exporta una lista de reproducción a un archivo M3U8 (M3U con codificación UTF-8).

    Args:
        db_conn: Conexión a la base de datos SQLite.
        playlist_id (int): El ID de la lista de reproducción a exportar.
        playlist_name (str): El nombre de la lista, para el nombre del archivo.
        output_dir (str): El directorio donde se guardará el archivo.

    Returns:
        str: La ruta completa al archivo M3U8 generado.
    """
    track_paths = _get_track_paths(db_conn, playlist_id)
    
    # Sanitizar el nombre de la playlist para que sea un nombre de archivo válido
    safe_filename = "".join([c for c in playlist_name if c.isalpha() or c.isdigit() or c in (' ', '-')]).rstrip()
    output_path = os.path.join(output_dir, f"{safe_filename}.m3u8")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for path in track_paths:
            # M3U estándar usa separadores de barra inclinada
            f.write(path.replace('\\', '/') + "\n")
            
    print(f"Playlist exportada a: {output_path}")
    return output_path

def export_to_csv(db_conn, playlist_id: int, playlist_name: str, output_dir: str) -> str:
    """
    Exporta una lista de reproducción a un archivo CSV.

    Args:
        db_conn: Conexión a la base de datos SQLite.
        playlist_id (int): El ID de la lista de reproducción a exportar.
        playlist_name (str): El nombre de la lista, para el nombre del archivo.
        output_dir (str): El directorio donde se guardará el archivo.

    Returns:
        str: La ruta completa al archivo CSV generado.
    """
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT t.title, t.artist, t.album, t.genre, t.year, t.bpm, t.key
        FROM tracks t
        JOIN smart_playlist_tracks spt ON t.id = spt.track_id
        WHERE spt.playlist_id = ?
    """, (playlist_id,))
    
    tracks_data = cursor.fetchall()
    
    safe_filename = "".join([c for c in playlist_name if c.isalpha() or c.isdigit() or c in (' ', '-')]).rstrip()
    output_path = os.path.join(output_dir, f"{safe_filename}.csv")
    
    headers = ["Title", "Artist", "Album", "Genre", "Year", "BPM", "Key"]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for track in tracks_data:
            writer.writerow([
                track['title'], track['artist'], track['album'], track['genre'],
                track['year'], track['bpm'], track['key']
            ])
            
    print(f"Playlist exportada a: {output_path}")
    return output_path

# Ejemplo de uso (requiere una base de datos poblada)
if __name__ == '__main__':
    # Esto es solo para demostración. Necesitarías una DB real.
    import sqlite3
    from core.database import get_db_path

    # Conectar a la DB
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print("Error: La base de datos no existe. Ejecute init_db() primero.")
    else:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Asumimos que existe una playlist con ID=1 y un nombre 'Test Playlist'
        TEST_PLAYLIST_ID = 1
        TEST_PLAYLIST_NAME = "My Test Playlist"
        OUTPUT_DIRECTORY = os.path.expanduser("~/Desktop") # Guardar en el escritorio

        print(f"Exportando playlist '{TEST_PLAYLIST_NAME}' (ID: {TEST_PLAYLIST_ID})")
        
        try:
            # Probar exportación a M3U8
            m3u_path = export_to_m3u(conn, TEST_PLAYLIST_ID, TEST_PLAYLIST_NAME, OUTPUT_DIRECTORY)
            print(f"M3U exportado a: {m3u_path}")

            # Probar exportación a CSV
            csv_path = export_to_csv(conn, TEST_PLAYLIST_ID, TEST_PLAYLIST_NAME, OUTPUT_DIRECTORY)
            print(f"CSV exportado a: {csv_path}")
        except Exception as e:
            print(f"Ocurrió un error durante la exportación de prueba: {e}")
            print("Asegúrese de que la playlist con ID=1 existe y tiene pistas asociadas.")

        conn.close() 