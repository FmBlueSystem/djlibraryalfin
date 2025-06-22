import os
import re
import hashlib
import secrets
from pathlib import Path
from typing import List, Set, Optional, Union
from cryptography.fernet import Fernet
import logging

class SecurityManager:
    """Gestión de seguridad para DjAlfin"""
    
    def __init__(self):
        self.key_file = Path.home() / ".djalfin" / "security.key"
        self.logger = logging.getLogger("security")
        self._ensure_key_exists()
        
        # Extensiones de archivo permitidas
        self.ALLOWED_AUDIO_EXTENSIONS = {
            '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.aiff'
        }
        
        # Caracteres peligrosos en nombres de archivo
        self.DANGEROUS_CHARS = {'..', '<', '>', '|', '"', '?', '*'}
        
        # Rutas prohibidas (patrones regex)
        self.FORBIDDEN_PATHS = [
            r'.*\.\./.*',  # Directory traversal
            r'^/etc/.*',   # System files Linux
            r'^/proc/.*',  # Process files Linux
            r'^/sys/.*',   # System files Linux
            r'^C:\\Windows\\.*',  # Windows system
            r'^C:\\Program Files\\.*',  # Program files
            r'^/System/.*',  # macOS system
            r'^/Library/.*',  # macOS library
        ]
    
    def _ensure_key_exists(self):
        """Asegurar que existe clave de cifrado"""
        try:
            if not self.key_file.exists():
                self.key_file.parent.mkdir(parents=True, exist_ok=True)
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                os.chmod(self.key_file, 0o600)  # Solo lectura para owner
                self.logger.info("New encryption key generated")
        except Exception as e:
            self.logger.error(f"Failed to create encryption key: {e}")
            raise
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Cifrar datos sensibles"""
        try:
            with open(self.key_file, 'rb') as f:
                key = f.read()
            
            fernet = Fernet(key)
            encrypted = fernet.encrypt(data.encode())
            return encrypted.decode('latin-1')  # Encoding seguro para bytes
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Descifrar datos sensibles"""
        try:
            with open(self.key_file, 'rb') as f:
                key = f.read()
            
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted_data.encode('latin-1'))
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def validate_file_path(self, file_path: Union[str, Path]) -> bool:
        """Validar que ruta de archivo es segura"""
        try:
            # Convertir a string si es Path
            path_str = str(file_path)
            
            # Verificar que no está vacío
            if not path_str or path_str.isspace():
                self.logger.warning("Empty or whitespace-only file path")
                return False
            
            # Resolver path absoluto
            try:
                abs_path = os.path.abspath(path_str)
            except Exception:
                self.logger.warning(f"Invalid path format: {path_str}")
                return False
            
            # Verificar patrones prohibidos
            for pattern in self.FORBIDDEN_PATHS:
                if re.match(pattern, abs_path, re.IGNORECASE):
                    self.logger.warning(f"Forbidden path pattern: {abs_path}")
                    return False
            
            # Verificar caracteres peligrosos
            for char in self.DANGEROUS_CHARS:
                if char in abs_path:
                    self.logger.warning(f"Dangerous character '{char}' in path: {abs_path}")
                    return False
            
            # Verificar que es un archivo existente
            if not os.path.isfile(abs_path):
                self.logger.warning(f"File does not exist: {abs_path}")
                return False
            
            # Verificar extensión permitida
            _, ext = os.path.splitext(abs_path)
            if ext.lower() not in self.ALLOWED_AUDIO_EXTENSIONS:
                self.logger.warning(f"Unsupported file extension: {ext}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"File path validation error: {e}")
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitizar nombre de archivo"""
        # Eliminar caracteres peligrosos
        sanitized = filename
        for char in self.DANGEROUS_CHARS:
            sanitized = sanitized.replace(char, '_')
        
        # Limitar longitud
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized
    
    def validate_directory_path(self, dir_path: Union[str, Path]) -> bool:
        """Validar que directorio es seguro"""
        try:
            path_str = str(dir_path)
            
            # Verificar que no está vacío
            if not path_str or path_str.isspace():
                return False
            
            # Resolver path absoluto
            abs_path = os.path.abspath(path_str)
            
            # Verificar patrones prohibidos
            for pattern in self.FORBIDDEN_PATHS:
                if re.match(pattern, abs_path, re.IGNORECASE):
                    self.logger.warning(f"Forbidden directory pattern: {abs_path}")
                    return False
            
            # Verificar que es un directorio
            if not os.path.isdir(abs_path):
                self.logger.warning(f"Directory does not exist: {abs_path}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Directory validation error: {e}")
            return False
    
    def scan_directory_safely(self, dir_path: Union[str, Path], max_files: int = 10000) -> List[str]:
        """Escanear directorio de forma segura"""
        if not self.validate_directory_path(dir_path):
            return []
        
        safe_files = []
        file_count = 0
        
        try:
            for root, dirs, files in os.walk(str(dir_path)):
                # Limitar número de archivos para prevenir DoS
                if file_count >= max_files:
                    self.logger.warning(f"Directory scan stopped at {max_files} files limit")
                    break
                
                for file in files:
                    file_path = os.path.join(root, file)
                    if self.validate_file_path(file_path):
                        safe_files.append(file_path)
                        file_count += 1
                        
                        if file_count >= max_files:
                            break
        
        except Exception as e:
            self.logger.error(f"Directory scan error: {e}")
        
        return safe_files
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generar token seguro"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: bytes = None) -> tuple[str, bytes]:
        """Hash seguro de contraseña con sal"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwdhash.hex(), salt
    
    def verify_password(self, password: str, hash_hex: str, salt: bytes) -> bool:
        """Verificar contraseña"""
        try:
            expected_hash = bytes.fromhex(hash_hex)
            pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return pwdhash == expected_hash
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    def is_safe_url(self, url: str) -> bool:
        """Verificar que URL es segura"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Solo HTTPS para APIs externas
            if parsed.scheme not in ['https', 'http']:
                return False
            
            # Verificar que no es localhost o IP privada
            hostname = parsed.hostname
            if hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                return False
            
            # Verificar IPs privadas básicas
            private_ranges = ['192.168.', '10.', '172.']
            if any(hostname.startswith(range_start) for range_start in private_ranges):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"URL validation error: {e}")
            return False

# Instancia global del manager de seguridad
security_manager = SecurityManager()

# Funciones de conveniencia
def validate_file_path(file_path: Union[str, Path]) -> bool:
    """Validar ruta de archivo (función de conveniencia)"""
    return security_manager.validate_file_path(file_path)

def sanitize_filename(filename: str) -> str:
    """Sanitizar nombre de archivo (función de conveniencia)"""
    return security_manager.sanitize_filename(filename)

def scan_directory_safely(dir_path: Union[str, Path], max_files: int = 10000) -> List[str]:
    """Escanear directorio de forma segura (función de conveniencia)"""
    return security_manager.scan_directory_safely(dir_path, max_files)

def encrypt_sensitive_data(data: str) -> str:
    """Cifrar datos sensibles (función de conveniencia)"""
    return security_manager.encrypt_sensitive_data(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Descifrar datos sensibles (función de conveniencia)"""
    return security_manager.decrypt_sensitive_data(encrypted_data)
