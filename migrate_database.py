#!/usr/bin/env python3
"""
Script de migración para actualizar la base de datos de DjAlfin
Agrega columnas faltantes a las tablas smart_playlists y smart_playlist_rules
"""

import sqlite3
import os

def migrate_database():
    """Migra la base de datos agregando columnas faltantes."""
    # Usar la misma ruta que DatabaseManager
    project_root = os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(project_root, "config")
    db_path = os.path.join(config_path, "library.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        print("   Ejecuta la aplicación primero para crear la base de datos.")
        return
    
    print(f"🔧 Iniciando migración de base de datos: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Migrar tabla smart_playlists
            migrate_smart_playlists_table(cursor, conn)
            
            # Migrar tabla smart_playlist_rules
            migrate_smart_playlist_rules_table(cursor, conn)
            
            print("🎉 Migración completada exitosamente.")
            
    except sqlite3.Error as e:
        print(f"❌ Error durante la migración: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def migrate_smart_playlists_table(cursor, conn):
    """Migra la tabla smart_playlists agregando columnas faltantes."""
    # Verificar si la tabla smart_playlists existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='smart_playlists'
    """)
    
    if not cursor.fetchone():
        print("⚠️  Tabla smart_playlists no existe. Se creará automáticamente.")
        return
    
    # Verificar columnas existentes
    cursor.execute("PRAGMA table_info(smart_playlists)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"📋 Columnas actuales en smart_playlists: {columns}")
    
    # Columnas requeridas para smart_playlists
    required_columns = [
        ('description', 'TEXT'),
        ('limit_count', 'INTEGER'),
        ('order_by', 'TEXT'),
        ('order_desc', 'BOOLEAN DEFAULT FALSE'),
        ('match_all', 'BOOLEAN DEFAULT TRUE'),
        ('auto_update', 'BOOLEAN DEFAULT TRUE'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    
    for column_name, column_type in required_columns:
        if column_name not in columns:
            print(f"➕ Agregando columna '{column_name}' a smart_playlists...")
            cursor.execute(f"""
                ALTER TABLE smart_playlists 
                ADD COLUMN {column_name} {column_type}
            """)
            conn.commit()
            print(f"✅ Columna '{column_name}' agregada exitosamente.")
        else:
            print(f"✅ Columna '{column_name}' ya existe en smart_playlists.")

def migrate_smart_playlist_rules_table(cursor, conn):
    """Migra la tabla smart_playlist_rules agregando columnas faltantes."""
    # Verificar si la tabla smart_playlist_rules existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='smart_playlist_rules'
    """)
    
    if not cursor.fetchone():
        print("⚠️  Tabla smart_playlist_rules no existe. Se creará automáticamente.")
        return
    
    # Verificar columnas existentes
    cursor.execute("PRAGMA table_info(smart_playlist_rules)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"📋 Columnas actuales en smart_playlist_rules: {columns}")
    
    # Columnas requeridas para smart_playlist_rules
    required_columns = [
        ('logical_operator', "TEXT DEFAULT 'and'"),
        ('rule_order', 'INTEGER DEFAULT 0'),
        ('value2', 'TEXT')
    ]
    
    for column_name, column_type in required_columns:
        if column_name not in columns:
            print(f"➕ Agregando columna '{column_name}' a smart_playlist_rules...")
            cursor.execute(f"""
                ALTER TABLE smart_playlist_rules 
                ADD COLUMN {column_name} {column_type}
            """)
            conn.commit()
            print(f"✅ Columna '{column_name}' agregada exitosamente.")
        else:
            print(f"✅ Columna '{column_name}' ya existe en smart_playlist_rules.")

if __name__ == "__main__":
    migrate_database()