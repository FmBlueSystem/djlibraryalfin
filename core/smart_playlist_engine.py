import sqlite3
import json

class SmartPlaylistEngine:
    """
    Motor para crear y gestionar listas de reproducción inteligentes.
    Convierte reglas legibles por humanos en consultas SQL.
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.operators = {
            "contains": "LIKE",
            "not_contains": "NOT LIKE",
            "is": "=",
            "is_not": "!=",
            "starts_with": "LIKE",
            "ends_with": "LIKE",
            "greater_than": ">",
            "less_than": "<",
            "is_in_range": "BETWEEN"
        }
        self.numeric_fields = ["bpm", "year", "duration", "rating"]

    def _format_value(self, field, operator, value):
        """Formatea el valor para la consulta SQL según el operador."""
        if field not in self.numeric_fields:
            str_value = str(value).replace("'", "''")
            if operator in ["contains", "not_contains"]:
                return f"'%{str_value}%'"
            elif operator == "starts_with":
                return f"'{str_value}%'"
            elif operator == "ends_with":
                return f"'%{str_value}'"
            return f"'{str_value}'"
        
        if operator == "is_in_range":
            try:
                low, high = map(float, value.split('-'))
                return f"{low} AND {high}"
            except (ValueError, IndexError):
                return "0 AND 0"
        
        # Para todos los demás operadores numéricos
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0 # Valor por defecto si no es un número válido

    def get_query_from_rules(self, rules, match_all=True):
        """
        Construye una consulta SQL a partir de una lista de reglas.
        """
        base_query = "SELECT * FROM tracks WHERE "
        conditions = []

        if not rules:
            return "SELECT * FROM tracks"

        for rule in rules:
            field = rule.get('field')
            operator_key = rule.get('operator')
            value = rule.get('value')

            if not all([field, operator_key, value]):
                continue

            if operator_key not in self.operators:
                continue

            sql_operator = self.operators[operator_key]
            
            # Usamos `f-string` para todo, ya que la sanitización se hace en _format_value
            # y esto simplifica la construcción de la condición.
            # Nos aseguramos de envolver los nombres de campo en ` ` para evitar conflictos con palabras clave de SQL.
            formatted_value = self._format_value(field, operator_key, value)
            
            if operator_key == "is_in_range":
                 conditions.append(f"`{field}` {sql_operator} {formatted_value}")
            else:
                 conditions.append(f"`{field}` {sql_operator} {formatted_value}")


        if not conditions:
            # Si ninguna regla es válida, devolvemos todas las pistas para no romper la preview.
            return "SELECT * FROM tracks"

        separator = " AND " if match_all else " OR "
        return base_query + separator.join(conditions)

    def get_tracks_for_rules(self, rules, match_all=True):
        """
        Ejecuta la consulta generada por las reglas y devuelve las pistas coincidentes.
        """
        query = self.get_query_from_rules(rules, match_all)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error al ejecutar la consulta de la Smart Playlist: {e}")
            print(f"Consulta problemática: {query}")
            return []
        finally:
            if conn:
                conn.close()

    def save_playlist(self, name, rules, match_all):
        """
        Guarda o actualiza una lista de reproducción inteligente en la base de datos.
        Utiliza una operación de "UPSERT" para manejar la creación y actualización.

        Args:
            name (str): El nombre de la lista de reproducción.
            rules (list): Una lista de diccionarios que representan las reglas.
            match_all (bool): True si todas las reglas deben coincidir, False si alguna debe coincidir.
        """
        conn = None
        try:
            conn = self._create_connection()
            cursor = conn.cursor()
            
            # Convertir la lista de reglas a una cadena JSON
            rules_json = json.dumps(rules)
            
            # Utilizar INSERT ON CONFLICT (UPSERT) para insertar o actualizar.
            # Si una playlist con el mismo nombre ya existe, se actualiza.
            query = """
            INSERT INTO smart_playlists (name, match_all, rules)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                match_all = excluded.match_all,
                rules = excluded.rules,
                updated_at = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(query, (name, 1 if match_all else 0, rules_json))
            conn.commit()
            print(f"Playlist '{name}' guardada exitosamente.")

        except sqlite3.Error as e:
            print(f"Error al guardar la playlist '{name}': {e}")
            raise  # Re-lanzar la excepción para que la UI pueda manejarla
        finally:
            if conn:
                conn.close()

    def get_playlist_details(self, playlist_id):
        """
        Obtiene los detalles (reglas y modo de concordancia) de una playlist específica.

        Args:
            playlist_id (int): El ID de la lista de reproducción.

        Returns:
            tuple: Una tupla (rules, match_all) o (None, None) si no se encuentra.
        """
        conn = None
        try:
            conn = self._create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT rules, match_all FROM smart_playlists WHERE id = ?", (playlist_id,))
            result = cursor.fetchone()
            if result:
                rules_json, match_all_int = result
                rules = json.loads(rules_json)
                match_all = bool(match_all_int)
                return rules, match_all
            return None, None
        except sqlite3.Error as e:
            print(f"Error al obtener detalles de la playlist {playlist_id}: {e}")
            return None, None
        finally:
            if conn:
                conn.close()

    def get_playlists(self):
        """Obtiene todas las listas de reproducción inteligentes de la base de datos."""
        conn = None
        try:
            conn = self._create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM smart_playlists ORDER BY name ASC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener las playlists: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _create_connection(self):
        """Crea y devuelve una conexión a la base de datos."""
        return sqlite3.connect(self.db_path)

# Ejemplo de uso (se eliminará o moverá a pruebas más adelante)
if __name__ == '__main__':
    # Asumimos que existe una DB 'library.db' en ../config/
    import os
    db_path_example = os.path.join(os.path.dirname(__file__), '..', 'config', 'library.db')

    # Crear una instancia del motor
    engine = SmartPlaylistEngine(db_path=db_path_example)

    # Definir un conjunto de reglas de ejemplo
    example_rules = [
        {'field': 'bpm', 'operator': 'between', 'value': [120, 125]},
        {'field': 'genre', 'operator': 'is', 'value': 'House'},
        {'field': 'key', 'operator': 'is_not', 'value': '5A'}
    ]

    # Generar la consulta
    sql_query = engine.get_query_from_rules(example_rules, match_all=True)
    print("--- Ejemplo de Consulta Generada ---")
    print("SQL:", sql_query)
    print("-" * 35)

    # Obtener las pistas que cumplen las reglas
    print("\n--- Obteniendo Pistas Coincidentes (usando AND) ---")
    matching_tracks = engine.get_tracks_for_rules(example_rules, match_all=True)
    if matching_tracks:
        print(f"Se encontraron {len(matching_tracks)} pistas.")
        print("Pistas:", matching_tracks)
    else:
        print("No se encontraron pistas que cumplan con TODAS las reglas.")
    print("-" * 35)
    
    # Obtener las pistas que cumplen las reglas con "ANY" (OR)
    print("\n--- Obteniendo Pistas Coincidentes (usando OR) ---")
    matching_tracks_any = engine.get_tracks_for_rules(example_rules, match_all=False)
    if matching_tracks_any:
        print(f"Se encontraron {len(matching_tracks_any)} pistas.")
        print("Pistas:", matching_tracks_any)
    else:
        print("No se encontraron pistas que cumplan con ALGUNA de las reglas.")
    print("-" * 35) 