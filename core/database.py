import sqlite3
import os

DB_FILE = "library.db"
CONFIG_DIR = "config"

def get_db_path():
    """Devuelve la ruta completa a la base de datos, asegurando que el directorio de configuración exista."""
    # Obtener la ruta del directorio raíz del proyecto
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, CONFIG_DIR)
    
    # Crear el directorio de configuración si no existe
    os.makedirs(config_path, exist_ok=True)
    
    return os.path.join(config_path, DB_FILE)

def create_connection():
    """Crea una conexión a la base de datos SQLite."""
    conn = None
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        print(f"Conexión a SQLite DB en {db_path} exitosa.")
    except sqlite3.Error as e:
        print(e)
    return conn

def init_db():
    """Inicializa la base de datos, creando las tablas necesarias si no existen."""
    conn = create_connection()
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
            cursor.execute("PRAGMA table_info(tracks)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'file_type' not in columns:
                cursor.execute("ALTER TABLE tracks ADD COLUMN file_type TEXT")

            conn.commit()
            print("Tabla 'tracks' creada o ya existente.")
        except sqlite3.Error as e:
            print(f"Error al crear la tabla: {e}")
        finally:
            conn.close()
    else:
        print("Error: No se pudo crear la conexión a la base de datos.")

def add_track(track_data):
    """Añade una nueva pista a la base de datos.
    
    Args:
        track_data (dict): Un diccionario con los metadatos de la pista.
                           Debe contener al menos 'file_path'.
    """
    conn = create_connection()
    if not conn:
        return

    # Mapeo de claves del diccionario a columnas de la base de datos
    # Se asegura de que todas las columnas existan en el diccionario, asignando None si no están.
    sql = ''' INSERT OR IGNORE INTO tracks(file_path, title, artist, album, genre, year, duration, bpm, key, comment, date_added, last_modified_date, last_scanned_date, file_type)
              VALUES(?,?,?,?,?,?,?,?,?,?,datetime('now'),?,?,?) '''
    
    track_values = (
        track_data.get('file_path'),
        track_data.get('title'),
        track_data.get('artist'),
        track_data.get('album'),
        track_data.get('genre'),
        track_data.get('year'),
        track_data.get('duration'),
        track_data.get('bpm'),
        track_data.get('key'),
        track_data.get('comment'),
        track_data.get('last_modified_date'),
        track_data.get('last_scanned_date'),
        track_data.get('file_type')
    )

    try:
        cursor = conn.cursor()
        cursor.execute(sql, track_values)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al añadir la pista {track_data.get('file_path')}: {e}")
    finally:
        conn.close()

def get_all_tracks():
    """Recupera todas las pistas de la base de datos."""
    conn = create_connection()
    if not conn:
        return []

    try:
        conn.row_factory = sqlite3.Row  # Devuelve filas que se pueden acceder por nombre de columna
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tracks ORDER BY artist, album, track_number")
        rows = cursor.fetchall()
        return [dict(row) for row in rows] # Convertir a lista de diccionarios
    except sqlite3.Error as e:
        print(f"Error al obtener las pistas: {e}")
        return []
    finally:
        conn.close()

def update_track_field(file_path, field, value):
    """
    Actualiza un campo específico para una pista en la base de datos.
    
    Args:
        file_path (str): La ruta del archivo de la pista a actualizar.
        field (str): El nombre de la columna a actualizar.
        value (any): El nuevo valor para el campo.
    """
    # Lista blanca de columnas que se pueden editar para seguridad.
    allowed_fields = ["title", "artist", "album", "genre", "year", "bpm", "key", "comment"]
    if field not in allowed_fields:
        print(f"Error: El campo '{field}' no es editable.")
        return

    sql = f"UPDATE tracks SET {field} = ? WHERE file_path = ?"
    
    conn = create_connection()
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
        conn.close()

def get_track_path(track_id):
    """
    Recupera la ruta de archivo de una pista dado su ID.

    Args:
        track_id (int): El ID de la pista.

    Returns:
        str: La ruta del archivo de la pista, o None si no se encuentra.
    """
    conn = create_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM tracks WHERE id = ?", (track_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Error al obtener la ruta de la pista {track_id}: {e}")
        return None
    finally:
        conn.close()

def get_track_by_path(file_path):
    """
    Recupera una pista de la base de datos usando su ruta de archivo.
    
    Args:
        file_path (str): La ruta completa del archivo de la pista.

    Returns:
        dict: Un diccionario con los datos de la pista si se encuentra, de lo contrario None.
    """
    conn = create_connection()
    if not conn:
        return None

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
        conn.close()

# Para probar la inicialización directamente
if __name__ == '__main__':
    init_db() 