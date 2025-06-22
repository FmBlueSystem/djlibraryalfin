import sqlite3
import os

DB_FILE = "library.db"
CONFIG_DIR = "config"

def get_db_path():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, CONFIG_DIR)
    os.makedirs(config_path, exist_ok=True)
    return os.path.join(config_path, DB_FILE)

def create_connection():
    conn = None
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        # print(f"Conexión a SQLite DB en {db_path} exitosa.") # Comentado para reducir verbosidad
    except sqlite3.Error as e:
        print(f"Error de conexión SQLite: {e}")
    return conn

def _add_column_if_not_exists(cursor, table_name, column_name, column_type):
    """Añade una columna a una tabla si no existe."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    if column_name not in columns:
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            print(f"Columna '{column_name}' añadida a la tabla '{table_name}'.")
        except sqlite3.Error as e:
            # Esto puede pasar si la columna ya existe pero PRAGMA no la listó (raro)
            # o si hay un error de sintaxis.
            print(f"Advertencia: No se pudo añadir la columna '{column_name}': {e}")

def create_smart_playlist_tables(cursor):
    """Crea las tablas para las listas de reproducción inteligentes si no existen."""
    try:
        # Tabla para almacenar la definición de cada Smart Playlist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                match_all INTEGER NOT NULL DEFAULT 1,
                rules TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Eliminar la tabla de reglas antigua si existe, ya que ahora se almacenan en JSON
        cursor.execute("DROP TABLE IF EXISTS smart_playlist_rules;")

        print("Tablas de listas inteligentes creadas o ya existentes.")
        # El commit se hará desde la función que llama a esta
    except sqlite3.Error as e:
        print(f"Error al crear las tablas de listas inteligentes: {e}")

def create_playlist_triggers(cursor):
    """Crea triggers para actualizar estadísticas de playlists automáticamente."""
    try:
        # Trigger para actualizar estadísticas después de insertar tracks
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_playlist_stats_insert
            AFTER INSERT ON playlist_tracks
            BEGIN
                UPDATE playlists SET 
                    track_count = (
                        SELECT COUNT(*) FROM playlist_tracks 
                        WHERE playlist_id = NEW.playlist_id
                    ),
                    duration = (
                        SELECT COALESCE(SUM(t.duration), 0) 
                        FROM playlist_tracks pt 
                        JOIN tracks t ON pt.track_id = t.id 
                        WHERE pt.playlist_id = NEW.playlist_id
                    ),
                    modified_date = datetime('now')
                WHERE id = NEW.playlist_id;
            END;
        """)
        
        # Trigger para actualizar estadísticas después de eliminar tracks
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_playlist_stats_delete
            AFTER DELETE ON playlist_tracks
            BEGIN
                UPDATE playlists SET 
                    track_count = (
                        SELECT COUNT(*) FROM playlist_tracks 
                        WHERE playlist_id = OLD.playlist_id
                    ),
                    duration = (
                        SELECT COALESCE(SUM(t.duration), 0) 
                        FROM playlist_tracks pt 
                        JOIN tracks t ON pt.track_id = t.id 
                        WHERE pt.playlist_id = OLD.playlist_id
                    ),
                    modified_date = datetime('now')
                WHERE id = OLD.playlist_id;
            END;
        """)
        
        print("Triggers de playlists creados correctamente.")
    except sqlite3.Error as e:
        print(f"Error creando triggers: {e}")

def init_db(conn=None):
    local_conn = False
    if conn is None:
        conn = create_connection()
        local_conn = True
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    genre TEXT,
                    year INTEGER,
                    track_number TEXT,
                    duration REAL,
                    bpm REAL,
                    key TEXT,
                    comment TEXT,
                    date_added TEXT NOT NULL,
                    last_modified_date REAL,
                    last_scanned_date REAL,
                    file_type TEXT
                );
            """)
            
            # === PLAYLISTS REGULARES ===
            # Tabla principal de playlists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT DEFAULT '',
                    created_date TEXT NOT NULL,
                    modified_date TEXT NOT NULL,
                    track_count INTEGER DEFAULT 0,
                    duration REAL DEFAULT 0.0,
                    is_favorite BOOLEAN DEFAULT 0,
                    color TEXT DEFAULT '#2196F3'
                );
            """)
            
            # Tabla de relación playlist-tracks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER NOT NULL,
                    track_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    added_date TEXT NOT NULL,
                    FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE,
                    FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE,
                    UNIQUE (playlist_id, track_id)
                );
            """)
            
            # Índices para mejor rendimiento
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_playlists_name ON playlists (name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks (playlist_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_playlist_tracks_position ON playlist_tracks (playlist_id, position);")
            
            # Añadir nuevas columnas si no existen (manejo simple de migración)
            _add_column_if_not_exists(cursor, "tracks", "file_type", "TEXT") # Ya estaba, pero mantenemos la lógica
            _add_column_if_not_exists(cursor, "tracks", "album_art_url", "TEXT")
            _add_column_if_not_exists(cursor, "tracks", "musicbrainz_recording_id", "TEXT")
            _add_column_if_not_exists(cursor, "tracks", "musicbrainz_artist_id", "TEXT")
            _add_column_if_not_exists(cursor, "tracks", "musicbrainz_release_id", "TEXT")
            _add_column_if_not_exists(cursor, "tracks", "spotify_track_id", "TEXT")
            _add_column_if_not_exists(cursor, "tracks", "spotify_artist_id", "TEXT")
            _add_column_if_not_exists(cursor, "tracks", "spotify_album_id", "TEXT")
            _add_column_if_not_exists(cursor, "tracks", "discogs_release_id", "TEXT")
            
            # Campos adicionales para análisis BPM avanzado
            _add_column_if_not_exists(cursor, "tracks", "bpm_confidence", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "beat_count", "INTEGER")
            _add_column_if_not_exists(cursor, "tracks", "rhythm_stability", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "bpm_analyzed_date", "TEXT")
            
            # Campos para características musicales avanzadas (AudioAnalyzer)
            _add_column_if_not_exists(cursor, "tracks", "energy", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "danceability", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "valence", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "acousticness", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "instrumentalness", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "liveness", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "speechiness", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "loudness", "REAL")
            
            # Características espectrales
            _add_column_if_not_exists(cursor, "tracks", "spectral_centroid", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "spectral_rolloff", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "zero_crossing_rate", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "mfcc_features", "TEXT")  # JSON string
            
            # Análisis de estructura
            _add_column_if_not_exists(cursor, "tracks", "beat_strength", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "rhythm_consistency", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "dynamic_range", "REAL")
            
            # Análisis DJ-específico
            _add_column_if_not_exists(cursor, "tracks", "intro_length", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "outro_length", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "mix_in_point", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "mix_out_point", "REAL")
            
            # Metadatos de análisis
            _add_column_if_not_exists(cursor, "tracks", "audio_analysis_confidence", "REAL")
            _add_column_if_not_exists(cursor, "tracks", "audio_features_version", "TEXT")
            _add_column_if_not_exists(cursor, "tracks", "audio_analyzed_date", "TEXT")

            # Crear las tablas de las listas inteligentes
            create_smart_playlist_tables(cursor)
            
            # Crear triggers para actualizar estadísticas automáticamente
            create_playlist_triggers(cursor)

            conn.commit()
            print("Tabla 'tracks' inicializada/actualizada correctamente.")
        except sqlite3.Error as e:
            print(f"Error al inicializar/actualizar la tabla 'tracks': {e}")
        finally:
            if local_conn:
                conn.close()
    else:
        print("Error: No se pudo crear la conexión a la base de datos para init_db.")

def add_track(track_data, conn=None):
    local_conn = False
    if conn is None:
        conn = create_connection()
        local_conn = True

    if not conn:
        print("Error: No se pudo crear la conexión a la base de datos para add_track.")
        return None

    # Lista de todos los campos posibles en la tabla (incluyendo los nuevos)
    # El orden debe coincidir con los VALUES y los SET de la cláusula ON CONFLICT
    fields = [
        'file_path', 'title', 'artist', 'album', 'genre', 'year', 'duration', 'bpm', 
        'key', 'comment', 'date_added', 'last_modified_date', 'last_scanned_date', 
        'file_type', 'album_art_url', 
        'musicbrainz_recording_id', 'musicbrainz_artist_id', 'musicbrainz_release_id',
        'spotify_track_id', 'spotify_artist_id', 'spotify_album_id',
        'discogs_release_id', 'bpm_confidence', 'beat_count', 'rhythm_stability', 'bpm_analyzed_date',
        # Campos de análisis de audio
        'energy', 'danceability', 'valence', 'acousticness', 'instrumentalness', 
        'liveness', 'speechiness', 'loudness',
        'spectral_centroid', 'spectral_rolloff', 'zero_crossing_rate', 'mfcc_features',
        'beat_strength', 'rhythm_consistency', 'dynamic_range',
        'intro_length', 'outro_length', 'mix_in_point', 'mix_out_point',
        'audio_analysis_confidence', 'audio_features_version', 'audio_analyzed_date'
    ]
    
    # Crear la lista de placeholders (?, ?, ...)
    placeholders = ', '.join(['?'] * len(fields))
    
    # Crear la lista de asignaciones para la cláusula DO UPDATE
    # Excluimos 'file_path' y 'date_added' de la actualización si el registro ya existe.
    # 'date_added' solo se establece en la inserción inicial.
    update_assignments = ', '.join([f"{field} = excluded.{field}" for field in fields if field not in ['file_path', 'date_added']])

    sql = f'''
        INSERT INTO tracks ({', '.join(fields)})
        VALUES ({placeholders})
        ON CONFLICT(file_path) DO UPDATE SET
            {update_assignments},
            last_scanned_date = datetime('now', 'localtime') -- Siempre actualizar last_scanned_date en un update
    '''
    
    # Preparar los valores. Usar track_data.get(field) para manejar campos faltantes (serán None/NULL)
    # Para 'date_added', si es una nueva inserción, se usa datetime('now').
    # Si es un update, 'date_added' no se cambia por la cláusula ON CONFLICT.
    # El placeholder para date_added en VALUES será datetime('now')
    
    track_values = []
    for field in fields:
        if field == 'date_added':
            # Este valor se usa para la inserción. Si hay conflicto, no se usa.
            # Usar datetime('now', 'localtime') para que coincida con el ON CONFLICT
            track_values.append(datetime_now_localtime_string()) 
        elif field == 'last_scanned_date':
             # Asegurar que last_scanned_date se actualice también en la inserción inicial
            track_values.append(datetime_now_localtime_string())
        else:
            track_values.append(track_data.get(field))
            
    track_id = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(track_values))
        conn.commit()
        
        # Después de la operación, obtener el ID de la fila afectada.
        # Si fue un INSERT, lastrowid es el nuevo ID.
        # Si fue un UPDATE, necesitamos obtenerlo con una consulta.
        if cursor.lastrowid > 0:
            track_id = cursor.lastrowid
        else:
            # Si fue un update, lastrowid es 0, así que consultamos el id.
            cursor.execute("SELECT id FROM tracks WHERE file_path = ?", (track_data['file_path'],))
            result = cursor.fetchone()
            if result:
                track_id = result[0]
                
    except sqlite3.Error as e:
        print(f"Error al añadir/actualizar la pista {track_data.get('file_path')}: {e}")
    finally:
        if local_conn:
            conn.close()

    return track_id

def datetime_now_localtime_string():
    """Devuelve la fecha y hora actual en formato string UTC para SQLite, compatible con datetime('now', 'localtime')."""
    # Esto es un poco un hack. SQLite con datetime('now', 'localtime') usa la zona horaria del sistema.
    # Para consistencia, es mejor manejar UTC o ser muy explícito.
    # Por ahora, para que coincida con el ON CONFLICT, simplemente llamaremos a una función que devuelva
    # el string que SQLite espera o usamos un valor que SQLite interpretará como "ahora en localtime".
    # La forma más simple es dejar que SQLite lo maneje en la inserción si el valor es None.
    # Sin embargo, la query ya tiene un placeholder para date_added y last_scanned_date.
    # Vamos a usar una función simple para obtener el string.
    # OJO: Esto puede no ser ideal para consistencia de zona horaria a largo plazo.
    # Sería mejor almacenar todo en UTC.
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_all_tracks(conn=None):
    local_conn = False
    if conn is None:
        conn = create_connection()
        local_conn = True

    if not conn:
        return []
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tracks ORDER BY artist, album, track_number, title") # Añadido title al ORDER BY
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error al obtener las pistas: {e}")
        return []
    finally:
        if local_conn:
            conn.close()

def update_track_field(file_path, field, value, conn=None):
    # Lista blanca de columnas que se pueden editar manualmente por el usuario.
    # Los campos de API (IDs, album_art_url) se actualizan mediante el escáner/enriquecedor.
    allowed_fields = [
        "title", "artist", "album", "genre", "year", "bpm", "key", "comment", "track_number"
    ]
    if field not in allowed_fields:
        print(f"Error: El campo '{field}' no es editable manualmente o no existe.")
        return

    sql = f"UPDATE tracks SET {field} = ? WHERE file_path = ?"
    
    local_conn = False
    if conn is None:
        conn = create_connection()
        local_conn = True

    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (value, file_path))
        conn.commit()
        print(f"Base de datos actualizada para {os.path.basename(file_path)}: {field} = {value}")
    except sqlite3.Error as e:
        print(f"Error al actualizar la base de datos: {e}")
    finally:
        if local_conn:
            conn.close()

def get_track_path(track_id, conn=None):
    local_conn = False
    if conn is None:
        conn = create_connection()
        local_conn = True
    
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM tracks WHERE id = ?", (track_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Error al obtener la ruta de la pista {track_id}: {e}")
        return None
    finally:
        if local_conn:
            conn.close()

def get_track_by_path(file_path, conn=None):
    local_conn = False
    if conn is None:
        conn = create_connection()
        local_conn = True

    if not conn: return None
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tracks WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error al buscar la pista por ruta {file_path}: {e}")
        return None
    finally:
        if local_conn:
            conn.close()

if __name__ == '__main__':
    print("Inicializando la base de datos desde __main__...")
    init_db()
    print("Base de datos lista.")

    # Ejemplo de cómo añadir una pista (para probar la nueva estructura)
    # conn = create_connection()
    # if conn:
    #     print("\nProbando añadir una pista de ejemplo...")
    #     sample_track_data = {
    #         'file_path': '/test/music/sample2.mp3', # Cambiado para evitar conflicto si se ejecuta varias veces
    #         'title': 'Sample Title 2',
    #         'artist': 'Sample Artist 2',
    #         'album': 'Sample Album 2',
    #         'genre': 'Test Genre; Rock',
    #         'year': 2025,
    #         'duration': 210.0,
    #         'bpm': 130.0,
    #         'key': '7m',
    #         'comment': 'This is another test track.',
    #         # 'date_added' y 'last_scanned_date' se manejan automáticamente
    #         'last_modified_date': datetime_now_localtime_string(), # Usar la función para consistencia
    #         'file_type': 'mp3',
    #         'album_art_url': 'http://example.com/art2.jpg',
    #         'musicbrainz_recording_id': 'mbrec-123-2',
    #         'musicbrainz_artist_id': 'mbart-xyz-2',
    #         'musicbrainz_release_id': 'mbrel-abc-2',
    #         'spotify_track_id': 'spot-456-2',
    #         'spotify_artist_id': 'spotart-def-2',
    #         'spotify_album_id': 'spotalb-ghi-2',
    #         'discogs_release_id': 'disc-789-2'
    #     }
    #     add_track(sample_track_data)
        
    #     print("\nRecuperando la pista de ejemplo:")
    #     retrieved_track = get_track_by_path('/test/music/sample2.mp3')
    #     if retrieved_track:
    #         for key, value in retrieved_track.items():
    #             print(f"  {key}: {value}")
    #     else:
    #         print("No se pudo recuperar la pista de ejemplo.")
        
    #     # Probar actualizarla
    #     print("\nProbando actualizar la pista de ejemplo...")
    #     update_data = {
    #         'file_path': '/test/music/sample2.mp3', # Clave para el ON CONFLICT
    #         'title': "Sample Title 2 Updated by Test",
    #         'album_art_url': 'http://example.com/art_updated2.jpg',
    #         'genre': 'Updated Rock; Metal'
    #         # No es necesario pasar todos los campos, solo los que cambian + file_path
    #     }
    #     add_track(update_data) # add_track maneja el UPSERT
    #     retrieved_track_updated = get_track_by_path('/test/music/sample2.mp3')
    #     if retrieved_track_updated:
    #         print(f"  Título actualizado: {retrieved_track_updated.get('title')}")
    #         print(f"  URL de arte actualizada: {retrieved_track_updated.get('album_art_url')}")
    #         print(f"  Género actualizado: {retrieved_track_updated.get('genre')}")
    #         print(f"  Fecha escaneo: {retrieved_track_updated.get('last_scanned_date')}")


    #     # Limpiar la pista de prueba si es necesario (ej. para ejecuciones repetidas de la prueba)
    #     # cursor = conn.cursor()
    #     # cursor.execute("DELETE FROM tracks WHERE file_path = ?", ('/test/music/sample2.mp3',))
    #     # conn.commit()
    #     # print("Pista de ejemplo eliminada.")

    #     conn.close()