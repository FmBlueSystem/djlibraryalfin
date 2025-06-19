"""Application configuration management."""

from __future__ import annotations

import json
import os
from typing import Any

CONFIG_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class AppConfig:
    """Simple JSON backed configuration handler."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from ``CONFIG_FILE`` or set defaults."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            else:
                self._config = {
                    "library_path": "",
                    "window_geometry": "1200x800",
                    "serpapi_api_key": "",
                    "discogs_user_token": "",
                    "sentry_dsn": "",
                }
                self.save()
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error al cargar config.json: {e}. Usando configuración por defecto.")
            self._config = {"library_path": "", "window_geometry": "1200x800", "serpapi_api_key": "", "discogs_user_token": "", "sentry_dsn": ""}

    def save(self) -> None:
        """Persist current configuration to ``CONFIG_FILE``."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
        except OSError as e:
            print(f"Error al guardar config.json: {e}")

    def get(self, key: str, default: Any | None = None) -> Any:
        """Return a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any, *, persist: bool = True) -> None:
        """Set a configuration value and optionally persist it."""
        self._config[key] = value
        if persist:
            self.save()

    def get_spotify_credentials(self):
        return self._config.get('spotify_client_id'), self._config.get('spotify_client_secret')

    def get_serpapi_api_key(self):
        return self._config.get('serpapi_api_key')

    def get_discogs_user_token(self):
        return self._config.get('discogs_user_token')
        
    def get_sentry_dsn(self):
        return self._config.get('sentry_dsn')

    def save_settings(self):
        """Guarda la configuración actual en el archivo JSON."""
        self._config['serpapi_api_key'] = self._config.get('serpapi_api_key', '')
        self._config['discogs_user_token'] = self._config.get('discogs_user_token', '')
        self._config['sentry_dsn'] = self._config.get('sentry_dsn', '')
        
        try:
            with open(CONFIG_FILE, 'w', encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
        except OSError as e:
            print(f"Error al guardar config.json: {e}")

