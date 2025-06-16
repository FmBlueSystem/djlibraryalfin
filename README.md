# Biblioteca de Audio Inteligente para DJs

Este proyecto busca ofrecer una herramienta de escritorio sencilla para organizar
bibliotecas musicales y preparar sesiones DJ. Se incluyen varios prototipos y
experimentos de interfaz en `ui/` y scripts de ejemplo en la raíz del
repositorio.

## Requisitos

- Python 3.12
- Dependencias listadas en `requirements.txt`
- Opcionalmente `python3-tk` para los componentes basados en Tkinter

Instala los paquetes de Python en un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Configuración

Copia `.env.example` a `.env` y rellena tus credenciales de Spotify y Discogs si
quieres utilizar las funciones de enriquecimiento de metadatos.

```bash
cp .env.example .env
```

Los ajustes de la aplicación se guardan en `config/config.json` y se gestionan a
través de la clase `AppConfig`.

## Pruebas

Las pruebas automatizadas se encuentran en el directorio `tests/` y se ejecutan
con:

```bash
python3 run_tests.py
```

Algunas pruebas requieren dependencias opcionales o acceso a un entorno gráfico;
en entornos mínimos podrían omitirse o fallar.

