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
                            energy REAL,
                            energy_tag REAL,
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
        sql = """ INSERT OR REPLACE INTO tracks(file_path, title, artist, album, genre, year, duration, bpm, key, energy, energy_tag, comment, date_added, last_modified_date, last_scanned_date, file_type)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),?,?,?) """

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
            track_data.get("energy"),
            track_data.get("energy_tag"),
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
                    print(
                        f"Error al añadir la pista {track_data.get('file_path')}: {e}"
                    )

    def get_all_tracks(self) -> List[Dict[str, Any]]:
        """Recupera todas las pistas de la base de datos."""
        with self._create_connection() as conn:
            if not conn:
                return []

            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM tracks ORDER BY artist, album, track_number"
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as e:
                print(f"Error al obtener las pistas: {e}")
                return []

    def get_track_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Busca una única pista por su file_path."""
        with self._create_connection() as conn:
            if not conn:
                return None
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tracks WHERE file_path = ?", (file_path,))
                row = cursor.fetchone()
                return dict(row) if row else None
            except sqlite3.Error as e:
                print(f"Error al buscar la pista {file_path}: {e}")
                return None

    def get_tracks_by_compatible_keys(
        self,
        keys: List[str],
        target_bpm: Optional[float] = None,
        tolerance_percent: float = 3.0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Busca pistas que coincidan con una lista de claves Camelot y, opcionalmente,
        un rango de BPM.
        """
        if not keys:
            return []

        # --- Construcción de la consulta ---
        base_sql = "SELECT * FROM tracks WHERE key IN ({}) AND key IS NOT NULL"
        placeholders = ",".join("?" for _ in keys)
        sql = base_sql.format(placeholders)
        params = list(keys)

        # Añadir filtro de BPM si se proporciona
        if target_bpm is not None:
            tolerance = target_bpm * (tolerance_percent / 100.0)
            bpm_min = target_bpm - tolerance
            bpm_max = target_bpm + tolerance
            sql += " AND bpm BETWEEN ? AND ?"
            params.extend([bpm_min, bpm_max])
            # Ordenar por proximidad de BPM si se usa el filtro
            sql += " ORDER BY ABS(bpm - ?), key"
            params.append(target_bpm)
        else:
            sql += " ORDER BY key, bpm"

        sql += " LIMIT ?"
        params.append(limit)

        with self._create_connection() as conn:
            if not conn:
                return []
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as e:
                print(f"Error al buscar por claves compatibles: {e}")
                return []

    def get_tracks_by_energy_range(
        self,
        target_energy: float,
        target_bpm: Optional[float] = None,
        tolerance_percent: float = 3.0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Busca pistas con un nivel de energía y, opcionalmente, un rango de BPM.
        """
        if target_energy is None:
            return []

        base_sql = "SELECT * FROM tracks WHERE energy IS NOT NULL"
        params = []

        # Filtro de Energía (ligeramente diferente para ordenar por él)
        energy_min = target_energy - 0.05  # Tolerancia fija para energía
        energy_max = target_energy + 0.05
        base_sql += " AND energy BETWEEN ? AND ?"
        params.extend([energy_min, energy_max])

        # Añadir filtro de BPM si se proporciona
        if target_bpm is not None:
            tolerance = target_bpm * (tolerance_percent / 100.0)
            bpm_min = target_bpm - tolerance
            bpm_max = target_bpm + tolerance
            base_sql += " AND bpm BETWEEN ? AND ?"
            params.extend([bpm_min, bpm_max])
            # Ordenar por proximidad de BPM primero
            base_sql += " ORDER BY ABS(bpm - ?), ABS(energy - ?)"
            params.extend([target_bpm, target_energy])
        else:
            base_sql += " ORDER BY ABS(energy - ?)"
            params.append(target_energy)

        base_sql += " LIMIT ?"
        params.append(limit)

        with self._create_connection() as conn:
            if not conn:
                return []
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(base_sql, tuple(params))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as e:
                print(f"Error al buscar por energía: {e}")
                return []

    def search_tracks(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Busca pistas cuyo título, artista o álbum contengan el término de búsqueda.
        La búsqueda no distingue entre mayúsculas y minúsculas.
        """
        if not search_term:
            return self.get_all_tracks()

        sql = """
            SELECT * FROM tracks
            WHERE LOWER(title) LIKE ?
               OR LOWER(artist) LIKE ?
               OR LOWER(album) LIKE ?
            ORDER BY artist, album, track_number
        """
        # El término de búsqueda se formatea para buscar subcadenas
        like_term = f"%{search_term.lower()}%"
        params = (like_term, like_term, like_term)

        with self._create_connection() as conn:
            if not conn:
                return []
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as e:
                print(f"Error al buscar pistas: {e}")
                return []

    def get_tracks_by_bpm_range(
        self, target_bpm: float, tolerance_percent: float = 3.0, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca pistas con un BPM dentro de un rango porcentual específico.
        """
        if target_bpm is None:
            return []

        tolerance = target_bpm * (tolerance_percent / 100.0)
        bpm_min = target_bpm - tolerance
        bpm_max = target_bpm + tolerance

        sql = """
            SELECT * FROM tracks
            WHERE bpm BETWEEN ? AND ?
            AND bpm IS NOT NULL
            ORDER BY ABS(bpm - ?)
            LIMIT ?
        """
        with self._create_connection() as conn:
            if not conn:
                return []
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, (bpm_min, bpm_max, target_bpm, limit))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as e:
                print(f"Error al buscar por BPM: {e}")
                return []

    def update_track_field(self, file_path: str, field: str, value: Any) -> None:
        """Actualiza un campo específico para una pista en la base de datos."""
        allowed_fields = [
            "title",
            "artist",
            "album",
            "genre",
            "year",
            "bpm",
            "key",
            "energy",
            "energy_tag",
            "comment",
        ]
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
    DatabaseManager()


# Para probar la inicialización directamente
if __name__ == "__main__":
    init_db()
