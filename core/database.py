import sqlite3
import os
from typing import Any, Dict, List, Optional, Tuple

DB_FILE = "library.db"
CONFIG_DIR = "config"

class DatabaseManager:
    def __init__(self):
        self.db_path = self._get_db_path()
        self._init_db()

    @staticmethod
    def _get_db_path() -> str:
        """Devuelve la ruta completa a la base de datos, asegurando que el directorio de configuración exista."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        config_path = os.path.join(project_root, CONFIG_DIR)
        os.makedirs(config_path, exist_ok=True)
        return os.path.join(config_path, DB_FILE)

    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Crea una conexión a la base de datos SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            print(f"Error de conexión a SQLite: {e}")
            return None

    def _init_db(self) -> None:
        """Inicializa la base de datos, creando las tablas necesarias si no existen."""
        with self._create_connection() as conn:
            if conn is not None:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
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
                    """
                    )
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"Error al crear la tabla: {e}")
            else:
                print("Error: No se pudo crear la conexión a la base de datos.")

    def add_track(self, track_data: Dict[str, Any]) -> None:
        """Añade una nueva pista a la base de datos."""
        sql = """ INSERT OR REPLACE INTO tracks(file_path, title, artist, album, genre, year, duration, bpm, key, comment, date_added, last_modified_date, last_scanned_date, file_type)
                  VALUES(?,?,?,?,?,?,?,?,?,?,datetime('now'),?,?,?) """
        
        track_values: Tuple[Any, ...] = (
            track_data.get("file_path"),
            track_data.get("title"),
            track_data.get("artist"),
            track_data.get("album"),
            track_data.get("genre"),
            track_data.get("year"),
            track_data.get("duration"),
            track_data.get("bpm"),
            track_data.get("key"),
            track_data.get("comment"),
            track_data.get("last_modified_date"),
            track_data.get("last_scanned_date"),
            track_data.get("file_type"),
        )

        with self._create_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql, track_values)
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"Error al añadir la pista {track_data.get('file_path')}: {e}")

    def get_all_tracks(self) -> List[Dict[str, Any]]:
        """Recupera todas las pistas de la base de datos."""
        with self._create_connection() as conn:
            if not conn:
                return []

            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tracks ORDER BY artist, album, track_number")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as e:
                print(f"Error al obtener las pistas: {e}")
                return []

    def update_track_field(self, file_path: str, field: str, value: Any) -> None:
        """Actualiza un campo específico para una pista en la base de datos."""
        allowed_fields = ["title", "artist", "album", "genre", "year", "bpm", "key", "comment"]
        if field not in allowed_fields:
            print(f"Error: El campo '{field}' no es editable.")
            return

        sql = f"UPDATE tracks SET {field} = ? WHERE file_path = ?"

        with self._create_connection() as conn:
            if not conn:
                return
            try:
                cursor = conn.cursor()
                cursor.execute(sql, (value, file_path))
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error al actualizar la base de datos: {e}")

def init_db():
    """Función de conveniencia para inicializar la db desde fuera si es necesario."""
    db_manager = DatabaseManager()

# Para probar la inicialización directamente
if __name__ == "__main__":
    init_db()
