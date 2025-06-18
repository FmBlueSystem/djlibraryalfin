import sqlite3
import os
import time
import random
import json
import string

# Añadir la raíz del proyecto al path para que los imports funcionen
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from core.database import init_db
from core.smart_playlist_engine import SmartPlaylistEngine

BENCHMARK_DB_PATH = os.path.join(os.path.dirname(__file__), 'benchmark_library.db')

def generate_mock_tracks(num_tracks):
    """Genera una lista de pistas falsas para pruebas de rendimiento."""
    tracks = []
    genres = ['House', 'Techno', 'Trance', 'Drum & Bass', 'Ambient', 'Hip Hop']
    keys = [f"{i}{j}" for i in range(1, 13) for j in ['A', 'B']]
    
    for i in range(num_tracks):
        track = (
            i,
            f"/music/fake_track_{i}.mp3",
            f"Track {i}",
            f"Artist {''.join(random.choices(string.ascii_uppercase, k=1))}",
            random.choice(genres),
            random.uniform(90.0, 160.0),
            random.choice(keys),
            random.randint(0, 100),
            f"202{random.randint(0, 4)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        )
        tracks.append(track)
    return tracks

def setup_benchmark_db(num_tracks):
    """Crea y puebla una base de datos de prueba en disco."""
    if os.path.exists(BENCHMARK_DB_PATH):
        os.remove(BENCHMARK_DB_PATH)
        
    print(f"Creando base de datos de benchmark con {num_tracks} pistas en: {BENCHMARK_DB_PATH}")
    
    conn = sqlite3.connect(BENCHMARK_DB_PATH)
    cursor = conn.cursor()
    
    # Crear esquema (una versión simplificada de init_db)
    cursor.execute("""
        CREATE TABLE tracks (
            id INTEGER PRIMARY KEY, file_path TEXT, title TEXT, artist TEXT, 
            genre TEXT, bpm REAL, key TEXT, play_count INTEGER, date_added TEXT
        );""")
    cursor.execute("CREATE INDEX idx_tracks_bpm ON tracks (bpm);")
    cursor.execute("CREATE INDEX idx_tracks_genre ON tracks (genre);")
    cursor.execute("CREATE INDEX idx_tracks_play_count ON tracks (play_count);")
    
    # Insertar datos en lotes para mayor eficiencia
    tracks = generate_mock_tracks(num_tracks)
    cursor.executemany("INSERT INTO tracks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", tracks)
    
    conn.commit()
    conn.close()
    print("Base de datos creada exitosamente.")

def benchmark_query_speed(engine, rules, num_runs=10):
    """Mide el tiempo promedio de ejecución de una consulta."""
    times = []
    for _ in range(num_runs):
        start_time = time.perf_counter()
        _ = engine.get_tracks_for_rules(rules, match_all=True)
        end_time = time.perf_counter()
        times.append(end_time - start_time)
    
    avg_time = sum(times) / num_runs
    print(f"  Tiempo promedio de consulta ({num_runs} ejecuciones): {avg_time * 1000:.2f} ms")
    return avg_time

def run_benchmarks(track_counts):
    """Ejecuta el conjunto de benchmarks para diferentes tamaños de biblioteca."""
    for count in track_counts:
        print("\n" + "="*50)
        print(f"INICIANDO BENCHMARK PARA {count:,} PISTAS")
        print("="*50)
        
        # 1. Preparar la base de datos
        setup_benchmark_db(count)
        
        # 2. Instanciar el motor
        engine = SmartPlaylistEngine(BENCHMARK_DB_PATH)
        
        # 3. Definir reglas de prueba
        print("\n[Benchmark 1: Consulta de BPM y Género]")
        rules1 = [
            {'field': 'bpm', 'operator': 'between', 'value': [120, 125]},
            {'field': 'genre', 'operator': 'is', 'value': 'Techno'}
        ]
        benchmark_query_speed(engine, rules1)

        print("\n[Benchmark 2: Consulta de Reproducciones y Tonalidad]")
        rules2 = [
            {'field': 'play_count', 'operator': 'greater_than', 'value': 80},
            {'field': 'key', 'operator': 'is', 'value': '8A'}
        ]
        benchmark_query_speed(engine, rules2)
        
        # Limpiar
        os.remove(BENCHMARK_DB_PATH)
        print(f"\nBase de datos de benchmark ({count} pistas) eliminada.")

if __name__ == '__main__':
    # Ejecutar benchmarks para 5k, 20k y 100k pistas
    TRACK_COUNTS_TO_TEST = [5_000, 20_000, 100_000]
    run_benchmarks(TRACK_COUNTS_TO_TEST) 