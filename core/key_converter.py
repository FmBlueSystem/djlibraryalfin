"""
Conversor de tonalidades musicales a notación Camelot.
La notación Camelot es un sistema usado por DJs para facilitar el mixing armónico.
"""

def musical_to_camelot(musical_key: str) -> str:
    """
    Convierte una tonalidad musical estándar a notación Camelot.
    
    Args:
        musical_key (str): Tonalidad en notación musical (ej: "Am", "F#", "Bb")
    
    Returns:
        str: Tonalidad en notación Camelot (ej: "8A", "2B", "6B")
    """
    if not musical_key or musical_key.strip() == "":
        return ""
    
    # Limpiar y normalizar la entrada
    key = musical_key.strip()
    
    # Mapeo completo de tonalidades musicales a Camelot
    # Tonalidades menores (A)
    minor_keys = {
        'Am': '8A', 'A♭m': '1A', 'Abm': '1A', 'G#m': '1A',
        'Em': '9A', 'E♭m': '2A', 'Ebm': '2A', 'D#m': '2A',
        'Bm': '10A', 'B♭m': '3A', 'Bbm': '3A', 'A#m': '3A',
        'F#m': '11A', 'Fm': '4A',
        'C#m': '12A', 'Cm': '5A',
        'Gm': '6A', 'Dm': '7A'
    }
    
    # Tonalidades mayores (B)
    major_keys = {
        'C': '8B', 'Cmaj': '8B',
        'A♭': '4B', 'Ab': '4B', 'Abmaj': '4B',
        'G': '9B', 'Gmaj': '9B',
        'E♭': '5B', 'Eb': '5B', 'Ebmaj': '5B', 'D#': '5B',
        'D': '10B', 'Dmaj': '10B',
        'B♭': '6B', 'Bb': '6B', 'Bbmaj': '6B', 'A#': '6B',
        'A': '11B', 'Amaj': '11B',
        'F': '7B', 'Fmaj': '7B',
        'E': '12B', 'Emaj': '12B',
        'B': '1B', 'Bmaj': '1B',
        'F#': '2B', 'F#maj': '2B',
        'C#': '3B', 'C#maj': '3B'
    }
    
    # Buscar en tonalidades menores primero
    if key in minor_keys:
        return minor_keys[key]
    
    # Buscar en tonalidades mayores
    if key in major_keys:
        return major_keys[key]
    
    # Si no se encuentra una coincidencia exacta, intentar normalizar
    # Convertir # a equivalentes con b
    normalized_key = normalize_key_notation(key)
    
    if normalized_key in minor_keys:
        return minor_keys[normalized_key]
    
    if normalized_key in major_keys:
        return major_keys[normalized_key]
    
    # Si no se puede convertir, devolver la tonalidad original
    return key

def normalize_key_notation(key: str) -> str:
    """
    Normaliza la notación de tonalidades para mejorar la coincidencia.
    
    Args:
        key (str): Tonalidad a normalizar
    
    Returns:
        str: Tonalidad normalizada
    """
    # Mapeo de equivalencias enarmónicas
    enharmonic_equivalents = {
        'G#': 'Ab', 'G#m': 'Abm', 'G#maj': 'Abmaj',
        'A#': 'Bb', 'A#m': 'Bbm', 'A#maj': 'Bbmaj',
        'C#': 'C#', 'C#m': 'C#m', 'C#maj': 'C#maj',  # Mantener C#
        'D#': 'Eb', 'D#m': 'Ebm', 'D#maj': 'Ebmaj',
        'F#': 'F#', 'F#m': 'F#m', 'F#maj': 'F#maj',  # Mantener F#
    }
    
    return enharmonic_equivalents.get(key, key)

def camelot_to_musical(camelot_key: str) -> str:
    """
    Convierte una tonalidad Camelot a notación musical estándar.
    
    Args:
        camelot_key (str): Tonalidad en notación Camelot (ej: "8A", "2B")
    
    Returns:
        str: Tonalidad en notación musical (ej: "Am", "F#")
    """
    if not camelot_key or camelot_key.strip() == "":
        return ""
    
    # Mapeo inverso de Camelot a musical
    camelot_to_musical_map = {
        # Tonalidades menores (A)
        '8A': 'Am', '1A': 'Abm', '9A': 'Em', '2A': 'Ebm',
        '10A': 'Bm', '3A': 'Bbm', '11A': 'F#m', '4A': 'Fm',
        '12A': 'C#m', '5A': 'Cm', '6A': 'Gm', '7A': 'Dm',
        
        # Tonalidades mayores (B)
        '8B': 'C', '4B': 'Ab', '9B': 'G', '5B': 'Eb',
        '10B': 'D', '6B': 'Bb', '11B': 'A', '7B': 'F',
        '12B': 'E', '1B': 'B', '2B': 'F#', '3B': 'C#'
    }
    
    return camelot_to_musical_map.get(camelot_key.strip(), camelot_key)

if __name__ == "__main__":
    # Pruebas del conversor
    test_keys = ['Am', 'F#m', 'Gm', 'B', 'C', 'Bb', 'D#m', 'A#']
    
    print("🎵 Pruebas de conversión Musical → Camelot:")
    for key in test_keys:
        camelot = musical_to_camelot(key)
        print(f"  {key} → {camelot}")
    
    print("\n🎵 Pruebas de conversión Camelot → Musical:")
    test_camelot = ['8A', '11A', '6A', '1B', '8B', '6B']
    for camelot in test_camelot:
        musical = camelot_to_musical(camelot)
        print(f"  {camelot} → {musical}") 