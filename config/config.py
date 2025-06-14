# config/config.py

import json
import os

CONFIG_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

class AppConfig:
    """
    Gestiona la configuración de la aplicación, guardada en un archivo JSON.
    """
    def __init__(self):
        self._config = {}
        self._load()

    def _load(self):
        """Carga la configuración desde el archivo JSON."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    self._config = json.load(f)
            else:
                # Valores por defecto si el archivo no existe
                self._config = {
                    'library_path': '',
                    'window_geometry': '1200x800'
                }
                self.save()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al cargar config.json: {e}. Usando configuración por defecto.")
            self._config = {'library_path': '', 'window_geometry': '1200x800'}

    def save(self):
        """Guarda la configuración actual en el archivo JSON."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=4)
        except IOError as e:
            print(f"Error al guardar config.json: {e}")

    def get(self, key, default=None):
        """Obtiene un valor de la configuración."""
        return self._config.get(key, default)

    def set(self, key, value):
        """Establece un valor en la configuración."""
        self._config[key] = value 