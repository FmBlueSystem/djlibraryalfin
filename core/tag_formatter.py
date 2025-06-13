"""
Módulo para formatear y estandarizar metadatos de pistas de audio.
Inspirado en la lógica de limpieza avanzada del proyecto 'nueva_biblioteca'.
"""

import re
from typing import Optional

# --- Constantes para el Formateo de Tags ---

# Géneros comunes que deben ser eliminados del título
COMMON_GENRES = {
    "Pop",
    "Rock",
    "Hip-Hop",
    "Hip Hop",
    "R&B",
    "RnB",
    "Dance",
    "Electronic",
    "House",
    "Techno",
    "Trance",
    "Dubstep",
    "Drum And Bass",
    "Jazz",
    "Blues",
    "Country",
    "Folk",
    "Metal",
    "Classical",
    "Latin",
    "Reggae",
    "Funk",
    "Soul",
}

# Sufijos que deben preservarse aunque contengan géneros (ej. "In The House")
PROTECTED_SUFFIXES = {
    "Original Mix",
    "Club Mix",
    "Radio Mix",
    "Extended Mix",
    "Remix",
    "Radio Edit",
    "Club Edit",
    "Instrumental",
    "Acapella",
    "Dub Mix",
    "VIP Mix",
    "Re-Edit",
    "Remaster",
    "Live Version",
    "Acoustic Version",
}

# Diccionarios de corrección estilística para formateo de tags
# La clave es el texto en PascalCase sin espacios, el valor es el formato deseado.
KNOWN_TITLES = {
    "StayinAlive": "Stayin' Alive",
    "Ymca": "YMCA",
    "RappersDelight": "Rapper's Delight",
    "GoodTimes": "Good Times",
}

KNOWN_ARTISTS = {
    "SugarHillGang": "Sugar Hill Gang",
    "TheBeeGees": "The Bee Gees",
    "KC&TheSunshineBand": "KC & The Sunshine Band",
    "AcDc": "AC/DC",
}

# Acrónimos que deben permanecer en mayúsculas en el formateo Title Case
KNOWN_ACRONYMS_TITLE_CASE = {"YMCA", "DJ", "UK", "USA", "EP", "LP", "MTV", "KC"}


def _to_pascal_case(text: str) -> str:
    """Convierte un texto a PascalCase, eliminando no alfanuméricos."""
    return "".join(word.capitalize() for word in re.split(r"\\W+", text) if word)


def _format_text_to_spaced_title_case(text: str) -> str:
    """Convierte una cadena a Title Case con espacios, manejando acrónimos y casos especiales."""
    if not text:
        return ""

    s = str(text)
    s = re.sub(r"[^a-zA-Z0-9\\s\'’-]+", " ", s)  # Conserva apóstrofes y guiones
    s = re.sub(r"[\\-_\\.\\(\\)]+", " ", s)  # Reemplaza separadores comunes
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"\\s+", " ", s).strip()

    words = s.split(" ")
    processed_words = []

    for word in words:
        if not word:
            continue

        upper_word = word.upper()
        if upper_word in KNOWN_ACRONYMS_TITLE_CASE:
            processed_words.append(upper_word)
        else:
            # Capitaliza partes de palabras con guiones/apóstrofes
            if "-" in word and len(word) > 1:
                processed_words.append(
                    "-".join([p.capitalize() for p in word.split("-")])
                )
            elif "'" in word and len(word) > 1:
                processed_words.append(
                    "'".join([p.capitalize() for p in word.split("'")])
                )
            else:
                processed_words.append(word.capitalize())

    return " ".join(processed_words)


def format_title_tag(raw_title: Optional[str]) -> str:
    """Formatea y limpia un título de canción."""
    if not raw_title:
        return "Unknown Title"

    cleaned_title = str(raw_title)

    # Extraer y preservar sufijos protegidos
    protected_suffix = ""
    for suffix in PROTECTED_SUFFIXES:
        match = re.search(
            rf"(\s*[-]?\s*\(?{re.escape(suffix)}\)?)$", cleaned_title, re.IGNORECASE
        )
        if match:
            protected_suffix = match.group(0)
            cleaned_title = cleaned_title[: match.start()].strip()
            break

    # Eliminar referencias a géneros del título principal
    for genre in COMMON_GENRES:
        cleaned_title = re.sub(
            rf"\s*\(?[\s-]*{re.escape(genre)}[\s-]*\)?\s*",
            "",
            cleaned_title,
            flags=re.IGNORECASE,
        )

    # Limpieza final y formateo
    pascal_key = _to_pascal_case(cleaned_title)
    if pascal_key in KNOWN_TITLES:
        main_formatted = KNOWN_TITLES[pascal_key]
    else:
        main_formatted = _format_text_to_spaced_title_case(cleaned_title)

    return (main_formatted + protected_suffix).strip()


def format_artist_tag(raw_artist: Optional[str]) -> str:
    """Formatea y limpia un nombre de artista."""
    if not raw_artist:
        return "Unknown Artist"

    cleaned_artist = str(raw_artist)

    pascal_key = _to_pascal_case(cleaned_artist)
    if pascal_key in KNOWN_ARTISTS:
        return KNOWN_ARTISTS[pascal_key]

    return _format_text_to_spaced_title_case(cleaned_artist)
