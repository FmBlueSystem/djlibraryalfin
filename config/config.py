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
                }
                self.save()
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error al cargar config.json: {e}. Usando configuración por defecto.")
            self._config = {"library_path": "", "window_geometry": "1200x800"}

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

