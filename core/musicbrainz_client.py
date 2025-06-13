import musicbrainzngs
from typing import Optional, Dict, Any

from .config_loader import load_musicbrainz_config


class MusicBrainzConfigurationError(Exception):
    """Excepción para errores de configuración de MusicBrainz."""
    pass


class MusicBrainzClient:
    """
    Cliente para interactuar con la API de MusicBrainz.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MusicBrainzClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            config = load_musicbrainz_config()
            if config:
                musicbrainzngs.set_useragent(
                    config["app_name"], config["app_version"], config["contact_email"]
                )
            else:
                # Aunque no es estrictamente necesario, lanzamos un error para ser consistentes
                # y para que el usuario sepa que la configuración no está completa.
                raise MusicBrainzConfigurationError(
                    "La configuración de MusicBrainz (app_name, app_version, contact_email) no se encontró en 'config.ini'. "
                    "Aunque no es estrictamente obligatorio, se recomienda configurarlo."
                )

            self.initialized = True

    def search_track(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """
        Busca una pista en MusicBrainz por título y artista.
        Devuelve un diccionario con metadatos enriquecidos.
        """
        try:
            # Buscamos grabaciones que coincidan
            result = musicbrainzngs.search_recordings(
                recording=title, artist=artist, limit=5
            )

            recordings = result.get("recording-list", [])
            if not recordings:
                return None

            # Nos quedamos con el primer resultado (el de mayor puntuación)
            best_match = recordings[0]

            enriched_data = {}

            # Extraer Género (de las etiquetas del artista, filtrando por relevancia)
            if "artist-credit" in best_match and best_match["artist-credit"]:
                artist_id = best_match["artist-credit"][0]["artist"]["id"]
                try:
                    # 'genres' no es un include válido, volvemos a 'tags'
                    artist_info = musicbrainzngs.get_artist_by_id(
                        artist_id, includes=["tags"]
                    )
                    tags = artist_info.get("artist", {}).get("tag-list", [])
                    
                    if tags:
                        # Priorizamos y filtramos los tags para encontrar un género real
                        # Ordenamos los tags por 'count' (popularidad) de mayor a menor
                        sorted_tags = sorted(tags, key=lambda t: t.get('count', 0), reverse=True)
                        
                        # Lista simple para excluir etiquetas obviamente incorrectas
                        blacklist = ["2008 universal fire victim"]

                        for tag in sorted_tags:
                            tag_name = tag.get("name", "").lower()
                            if tag_name and tag_name not in blacklist:
                                enriched_data["genre"] = tag_name.title()
                                break # Nos quedamos con el primer género válido y más popular
                except musicbrainzngs.ResponseError:
                    # Si la llamada a get_artist_by_id falla, simplemente no añadimos el género
                    pass

            # Extraer Año de lanzamiento
            if "release-list" in best_match and best_match["release-list"]:
                first_release = best_match["release-list"][0]
                if "date" in first_release and first_release["date"]:
                    enriched_data["year"] = first_release["date"].split("-")[0]

            # Extraer Sello discográfico
            if "release-list" in best_match and best_match["release-list"]:
                release_id = best_match["release-list"][0]["id"]
                release_info = musicbrainzngs.get_release_by_id(
                    release_id, includes=["labels"]
                )
                labels = release_info.get("release", {}).get("label-info-list", [])
                if labels:
                    enriched_data["label"] = labels[0].get("label", {}).get("name")

            return enriched_data

        except musicbrainzngs.ResponseError as e:
            # Un error de respuesta puede indicar un problema de autenticación o de la solicitud
            raise MusicBrainzConfigurationError(f"Error en la respuesta de MusicBrainz. Revisa la configuración y la conexión. Detalles: {e}")
        except musicbrainzngs.MusicBrainzError as e:
            print(f"Error al buscar en MusicBrainz: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado con MusicBrainz: {e}")
            return None


if __name__ == "__main__":
    # Código de prueba
    print("--- Probando cliente de MusicBrainz ---")
    client = MusicBrainzClient()

    test_title = "Bohemian Rhapsody"
    test_artist = "Queen"

    print(f"Buscando '{test_title}' de '{test_artist}'...")
    data = client.search_track(test_title, test_artist)

    if data:
        print("Datos enriquecidos encontrados:")
        for key, value in data.items():
            print(f"  - {key.title()}: {value}")
    else:
        print("No se encontraron datos.")
