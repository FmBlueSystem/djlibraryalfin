from pydub import AudioSegment
from typing import List

def generate_waveform_data(file_path: str, num_points: int = 400) -> List[float]:
    """
    Genera una lista de puntos de datos para la forma de onda de un archivo de audio.

    Args:
        file_path (str): La ruta al archivo de audio.
        num_points (int): El número de puntos de datos a generar para la visualización.

    Returns:
        list: Una lista de floats normalizados (0.0 a 1.0) que representan la amplitud.
              Devuelve una lista vacía si hay un error.
    """
    try:
        audio = AudioSegment.from_file(file_path)

        # Convertir a mono para simplificar el análisis de la amplitud
        audio = audio.set_channels(1)

        # Duración de cada "slice" de audio a promediar
        if num_points == 0:
            return []
        slice_duration_ms = len(audio) / num_points
        if slice_duration_ms == 0:
            return []

        waveform_points: List[float] = []
        for i in range(num_points):
            start_ms = i * slice_duration_ms
            end_ms = (i + 1) * slice_duration_ms
            audio_slice = audio[start_ms:end_ms]

            # Usamos el valor RMS (Root Mean Square) como medida de la "potencia" o "volumen"
            # del slice. Es una buena aproximación de la amplitud percibida.
            rms = audio_slice.rms

            # Evitar división por cero si el slice está en silencio
            if rms > 0:
                waveform_points.append(rms)
            else:
                waveform_points.append(0.0)

        # Normalizar los puntos de 0.0 a 1.0
        max_rms = max(waveform_points) if waveform_points else 1.0
        if max_rms == 0:
            max_rms = 1.0  # Evitar división por cero en un archivo completamente silencioso

        normalized_points: List[float] = [point / max_rms for point in waveform_points]

        return normalized_points

    except Exception as e:
        print(f"Error al generar la forma de onda para {file_path}: {e}")
        return [] 