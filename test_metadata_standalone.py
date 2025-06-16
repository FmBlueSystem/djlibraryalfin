#!/usr/bin/env python3
# test_metadata_standalone.py - Prueba independiente de la lógica de enriquecimiento de metadatos.

import sys
import os
from dotenv import load_dotenv
from pprint import pprint # Para imprimir diccionarios de forma legible

# Añadir el directorio raíz del proyecto al PYTHONPATH
# Esto es necesario para que los imports funcionen cuando se ejecuta este script directamente.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.metadata_enricher import enrich_metadata

def run_enrichment_tests():
    """Ejecuta pruebas de enriquecimiento para varias pistas de ejemplo."""
    
    # Cargar variables de entorno desde .env (si existe)
    # Esto es crucial para que los clientes de API puedan autenticarse.
    # Asegúrate de tener un archivo .env con tus credenciales.
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        print(f"Cargando variables de entorno desde: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        print("Advertencia: Archivo .env no encontrado. Las APIs podrían no funcionar.")
        print("Por favor, copia .env.example a .env y añade tus credenciales.")

    # Los clientes de API (Spotify, Discogs, MusicBrainz) se inicializan
    # al importar sus módulos o al usarlos por primera vez,
    # cargando credenciales desde las variables de entorno (ver load_dotenv arriba).
    print("-" * 30)

    sample_tracks = [
        {
            "title": "Bohemian Rhapsody",
            "artist": "Queen",
            "album": "A Night at the Opera",
            "genre": "Rock", # Género local
            "comment": "Local comment for Queen track" # Comentario local
        },
        {
            "title": "Stairway to Heaven",
            "artist": "Led Zeppelin",
            # Sin álbum, para ver si lo encuentra
        },
        {
            "title": "Like a Rolling Stone",
            "artist": "Bob Dylan",
            "year": 1965 # Año local
        },
        {
            "title": "One", # Este puede ser ambiguo, U2 o Metallica, etc.
            "artist": "U2",
            "album": "Achtung Baby"
        },
        { 
            "title": "The Sound of Silence", # Para probar Discogs y Spotify
            "artist": "Simon & Garfunkel"
        },
        { 
            "title": "Smells Like Teen Spirit", 
            "artist": "Nirvana",
            # Sin ID de MusicBrainz para forzar búsqueda y ver si lo añade
        },
        { 
            "title": "Yesterday",
            "artist": "The Beatles"
        },
        { 
            "title": "Get Lucky",
            "artist": "Daft Punk",
            "album": "Random Access Memories",
            "genre": "Funk; Disco; Electronic", # Género local detallado
            "year": 2013,
            "bpm": 116, # BPM local
            "key": "F#m", # Tonalidad local
            "comment": "This is a local comment that should be preserved."
        },
        { 
            "title": "An Ending (Ascent)",
            "artist": "Brian Eno",
            "album": "Apollo: Atmospheres and Soundtracks"
        },
        { # Pista con un nombre de artista/título que podría no ser fácil de encontrar
            "title": "保護司", # Título en japonés
            "artist": "ずっと真夜中でいいのに。" # Artista en japonés
        },
        { # Pista con información muy específica que podría estar en Discogs
            "title": "Shine On You Crazy Diamond (Pts. 1-5)",
            "artist": "Pink Floyd",
            "album": "Wish You Were Here"
        }
    ]

    for i, track_info_original in enumerate(sample_tracks):
        print(f"\n===== PISTA DE PRUEBA #{i+1} =====")
        print("Metadatos Originales (track_info_local):")
        pprint(track_info_original)
        
        # Hacemos una copia para no modificar el original en la lista de sample_tracks
        # Esto simula el track_info_local.copy() que se pasa a enrich_metadata
        track_info_to_enrich = track_info_original.copy() 
        
        print("\n--- Enriqueciendo... ---")
        # Esto simula: api_derived_data = enrich_metadata(track_info_local.copy())
        api_derived_data = enrich_metadata(track_info_to_enrich) 
        
        print("\nMetadatos Derivados de API (Resultado de enrich_metadata):")
        pprint(api_derived_data)

        # Simular la lógica de fusión que ocurre en library_scanner.py:
        # final_data_for_db = api_derived_data.copy()
        # final_data_for_db.update(track_info_local)
        
        final_merged_data = api_derived_data.copy()
        final_merged_data.update(track_info_original) # Los datos locales (originales) tienen prioridad

        print("\nMetadatos Finales Fusionados (Local > API para campos comunes):")
        pprint(final_merged_data)
        print("-" * 70)

if __name__ == '__main__':
    print("Iniciando prueba independiente de enriquecimiento de metadatos...")
    print("Asegúrate de tener un archivo .env con tus credenciales de API (Spotify, Discogs).")
    print("Puedes copiar .env.example a .env y rellenarlo.")
    print("La prueba puede tardar un poco debido a las llamadas a las APIs externas.")
    print("-" * 70)
    
    run_enrichment_tests()
    
    print("\n" + "=" * 70)
    print("Prueba de enriquecimiento finalizada.")
    print("Revisa la salida para verificar que los datos se fusionaron correctamente.")
    print("Comprueba si se obtuvieron IDs (MusicBrainz, Spotify, Discogs) y URLs de arte de portada.")
    print("Verifica que los campos locales (ej. 'comment', 'bpm', 'key' en 'Get Lucky') se preservaron.")
    print("Observa cómo se manejan los géneros (curación y fusión).")
    print("=" * 70)
