"""Secure configuration management with encryption for sensitive data."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Set
from pathlib import Path
import logging

from core.security import SecurityManager, encrypt_sensitive_data, decrypt_sensitive_data

class SecureConfig:
    """Configuration manager with encrypted storage for sensitive data"""
    
    # Keys that should be encrypted
    SENSITIVE_KEYS = {
        'serpapi_api_key',
        'discogs_user_token', 
        'sentry_dsn',
        'spotify_client_id',
        'spotify_client_secret',
        'lastfm_api_key',
        'database_password',
        'api_tokens'
    }
    
    def __init__(self, config_file: str = None):
        self.logger = logging.getLogger("secure_config")
        self.config_dir = Path.home() / ".djalfin"
        self.config_dir.mkdir(exist_ok=True)
        
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = self.config_dir / "config.json"
        
        self.security_manager = SecurityManager()
        self._config: Dict[str, Any] = {}
        self._encrypted_config: Dict[str, str] = {}  # Store encrypted values
        self._load()
    
    def _load(self) -> None:
        """Load configuration from file with decryption"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Separate encrypted and plain data
                self._config = data.get("plain", {})
                self._encrypted_config = data.get("encrypted", {})
                
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self._set_defaults()
                self.save()
                self.logger.info("Created new configuration with defaults")
                
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error(f"Error loading configuration: {e}")
            self._set_defaults()
    
    def _set_defaults(self) -> None:
        """Set default configuration values"""
        self._config = {
            "library_path": "",
            "window_geometry": "1200x800",
            "log_level": "INFO",
            "auto_scan_library": True,
            "theme": "dark",
            "language": "es",
            "max_recent_files": 10,
            "audio_buffer_size": 1024,
            "enable_sentry": True,
            "check_for_updates": True
        }
        self._encrypted_config = {}
    
    def save(self) -> None:
        """Save configuration to file with encryption"""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Combine plain and encrypted data
            data = {
                "plain": self._config,
                "encrypted": self._encrypted_config,
                "version": "1.0",
                "encrypted_keys": list(self.SENSITIVE_KEYS)
            }
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            # Set secure file permissions
            os.chmod(self.config_file, 0o600)
            self.logger.info("Configuration saved successfully")
            
        except OSError as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with automatic decryption"""
        try:
            # Check if it's a sensitive key that should be encrypted
            if key in self.SENSITIVE_KEYS:
                if key in self._encrypted_config:
                    encrypted_value = self._encrypted_config[key]
                    if encrypted_value:  # Don't decrypt empty strings
                        return decrypt_sensitive_data(encrypted_value)
                return default
            else:
                return self._config.get(key, default)
                
        except Exception as e:
            self.logger.error(f"Error getting config value '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """Set configuration value with automatic encryption"""
        try:
            if key in self.SENSITIVE_KEYS:
                # Encrypt sensitive data
                if value and str(value).strip():  # Don't encrypt empty values
                    encrypted_value = encrypt_sensitive_data(str(value))
                    self._encrypted_config[key] = encrypted_value
                else:
                    # Remove key if value is empty
                    self._encrypted_config.pop(key, None)
            else:
                # Store plain data
                self._config[key] = value
            
            if persist:
                self.save()
                
        except Exception as e:
            self.logger.error(f"Error setting config value '{key}': {e}")
            raise
    
    def delete(self, key: str, persist: bool = True) -> bool:
        """Delete configuration value"""
        deleted = False
        
        if key in self.SENSITIVE_KEYS:
            if key in self._encrypted_config:
                del self._encrypted_config[key]
                deleted = True
        else:
            if key in self._config:
                del self._config[key]
                deleted = True
        
        if deleted and persist:
            self.save()
        
        return deleted
    
    def get_all_keys(self) -> Set[str]:
        """Get all configuration keys"""
        return set(self._config.keys()) | set(self._encrypted_config.keys())
    
    def has_key(self, key: str) -> bool:
        """Check if configuration key exists"""
        if key in self.SENSITIVE_KEYS:
            return key in self._encrypted_config
        else:
            return key in self._config
    
    def export_config(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Export configuration (optionally including decrypted sensitive data)"""
        exported = self._config.copy()
        
        if include_sensitive:
            for key in self._encrypted_config:
                try:
                    exported[key] = self.get(key)
                except Exception as e:
                    self.logger.error(f"Error decrypting {key} for export: {e}")
                    exported[key] = "[DECRYPTION_ERROR]"
        else:
            # Just show that sensitive keys exist
            for key in self._encrypted_config:
                exported[key] = "[ENCRYPTED]"
        
        return exported
    
    def import_config(self, config_data: Dict[str, Any], overwrite: bool = False) -> None:
        """Import configuration data"""
        for key, value in config_data.items():
            if not overwrite and self.has_key(key):
                continue
            self.set(key, value, persist=False)
        
        self.save()
        self.logger.info(f"Imported {len(config_data)} configuration values")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self._set_defaults()
        self.save()
        self.logger.info("Configuration reset to defaults")
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return issues"""
        issues = {
            "errors": [],
            "warnings": [],
            "missing_required": []
        }
        
        # Check library path
        library_path = self.get("library_path")
        if library_path and not os.path.exists(library_path):
            issues["errors"].append(f"Library path does not exist: {library_path}")
        
        # Check for missing sensitive keys that might be required
        required_for_features = {
            "sentry_dsn": "Error tracking",
            "serpapi_api_key": "Music search functionality",
            "discogs_user_token": "Music metadata lookup"
        }
        
        for key, feature in required_for_features.items():
            if not self.get(key):
                issues["warnings"].append(f"{feature} disabled: {key} not configured")
        
        # Validate window geometry
        geometry = self.get("window_geometry", "")
        if geometry and "x" not in geometry:
            issues["errors"].append(f"Invalid window geometry format: {geometry}")
        
        return issues
    
    # Convenience methods for specific config values
    def get_library_path(self) -> str:
        return self.get("library_path", "")
    
    def set_library_path(self, path: str) -> None:
        # Validate path before setting
        if path and not os.path.exists(path):
            raise ValueError(f"Library path does not exist: {path}")
        self.set("library_path", path)
    
    def get_sentry_dsn(self) -> str:
        return self.get("sentry_dsn", "")
    
    def get_serpapi_api_key(self) -> str:
        return self.get("serpapi_api_key", "")
    
    def get_discogs_user_token(self) -> str:
        return self.get("discogs_user_token", "")
    
    def get_spotify_credentials(self) -> tuple[str, str]:
        client_id = self.get("spotify_client_id", "")
        client_secret = self.get("spotify_client_secret", "")
        return client_id, client_secret
    
    def set_spotify_credentials(self, client_id: str, client_secret: str) -> None:
        self.set("spotify_client_id", client_id, persist=False)
        self.set("spotify_client_secret", client_secret, persist=True)
    
    def is_sentry_enabled(self) -> bool:
        return self.get("enable_sentry", True) and bool(self.get_sentry_dsn())
    
    def get_log_level(self) -> str:
        return self.get("log_level", "INFO").upper()
    
    def get_lastfm_api_key(self) -> str:
        return self.get("lastfm_api_key", "")
    
    def set_lastfm_api_key(self, api_key: str) -> None:
        self.set("lastfm_api_key", api_key)

# Global secure config instance
secure_config = SecureConfig()

# Migration function from old config
def migrate_from_old_config(old_config_file: str) -> bool:
    """Migrate from old plain-text config to secure config"""
    try:
        if not os.path.exists(old_config_file):
            return False
        
        with open(old_config_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        
        # Import all data (sensitive data will be encrypted automatically)
        secure_config.import_config(old_data, overwrite=True)
        
        # Backup old config
        backup_file = old_config_file + ".backup"
        os.rename(old_config_file, backup_file)
        
        logging.info(f"Migrated configuration from {old_config_file} to secure storage")
        logging.info(f"Old config backed up to {backup_file}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to migrate configuration: {e}")
        return False
