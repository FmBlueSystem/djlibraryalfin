# Documentación Completa de Funcionalidades - DjAlfin

Este documento detalla todas las características implementadas en la aplicación DjAlfin, incluyendo tanto las funcionalidades visibles y accesibles desde la interfaz de usuario como aquellas que existen en el backend (`core`) pero que aún no han sido conectadas.

---

## 1. Funcionalidades Principales (Visibles en la Interfaz)

Estas son las características que un usuario puede utilizar directamente en la aplicación.

### 1.1. Gestión de la Biblioteca Musical
- **Escaneo de Biblioteca:** Importa archivos de audio (`.mp3`, `.wav`, etc.) desde carpetas locales.
- **Base de Datos Centralizada:** Utiliza SQLite para almacenar y gestionar todos los metadatos de la biblioteca de forma persistente.
- **Vista de Pistas:** Una tabla principal muestra toda la biblioteca con columnas para Título, Artista, BPM, Tono, etc.
- **Ordenamiento:** Permite ordenar la biblioteca haciendo clic en las cabeceras de las columnas.
- **Búsqueda Rápida:** Un campo de texto filtra toda la biblioteca en tiempo real para encontrar canciones por cualquier metadato.

### 1.2. Edición y Gestión de Metadatos
- **Panel de Metadatos:** Al seleccionar una pista, un panel lateral muestra sus metadatos.
- **Edición Directa:** Permite editar campos como Título, Artista, Álbum, Género y Comentarios.
- **Guardado en Archivo:** Los metadatos modificados se guardan tanto en la base de datos de la aplicación como en las etiquetas del propio archivo de audio (ID3, etc.).
- **Análisis de BPM:** Un botón en el panel de reproducción permite analizar la canción cargada y guardar su BPM.

### 1.3. Reproducción de Audio
- **Controles Esenciales:** Funciones de **Play / Pausa / Stop**.
- **Barra de Progreso (Seek):** Permite visualizar y saltar a cualquier punto de la canción.
- **Contadores de Tiempo:** Muestra el tiempo transcurrido y la duración total de la pista.
- **Atajos de Teclado:** Control de Play/Pausa (Espacio) y Volumen (Flechas arriba/abajo).

### 1.4. Playlists
- **Playlists Manuales:** Permite la creación de playlists a las que se pueden añadir canciones (la adición de canciones aún debe ser implementada en la UI).
- **Playlists Inteligentes:** Crea playlists automáticas basadas en reglas definidas por el usuario (ej. "Género es 'House' Y BPM > 125").
- **Editor de Reglas:** Incluye una interfaz para construir y modificar las reglas de las playlists inteligentes.

### 1.5. Interfaz de Usuario
- **Tema Profesional Oscuro:** Interfaz moderna inspirada en software de DJ.
- **Diseño Redimensionable:** Los paneles se pueden ajustar usando divisores (splitters).
- **Barra de Estado:** Proporciona notificaciones sobre las operaciones de la aplicación.

---

## 2. Funcionalidades de Integración API (Backend Implementado, UI Desconectada)

Estas funciones existen en el `core` de la aplicación y están listas para ser usadas, pero no hay un botón o menú en la interfaz para activarlas.

### 2.1. Objetivo General: Enriquecimiento de Metadatos
El propósito de estas funciones es conectarse a servicios en línea para obtener metadatos de alta calidad y completar automáticamente la información de las pistas de la biblioteca.

### 2.2. Módulo `core/discogs_client.py`
- **Función:** Se conecta a la API de **Discogs**, una de las bases de datos de música más completas del mundo.
- **Capacidades:** 
    - Buscar canciones por artista y título.
    - Obtener metadatos precisos como el año de lanzamiento, el sello discográfico y el arte del álbum.
- **Estado:** La lógica está implementada y funcional, pero no se llama desde ninguna parte de la UI.

### 2.3. Módulo `core/spotify_client.py`
- **Función:** Se conecta a la API web de **Spotify** usando la librería `spotipy`.
- **Capacidades:**
    - Buscar pistas en el catálogo de Spotify.
    - Obtener el arte del álbum en alta resolución.
    - Obtener métricas de audio de Spotify: `bailabilidad` (danceability), `energía` (energy), `valencia` (positividad), y `popularidad`.
- **Estado:** La lógica está implementada y funcional, a la espera de ser conectada.

### 2.4. Módulo `core/metadata_enricher.py`
- **Función:** Actúa como el orquestador que utiliza los clientes de API.
- **Flujo de Trabajo:**
    1. Recibe una pista de la biblioteca local.
    2. Utiliza `DiscogsClient` y `SpotifyClient` para buscar la pista en línea.
    3. Compara los resultados y selecciona los mejores datos disponibles.
    4. Actualiza la pista en la base de datos local con la información "enriquecida".
- **Estado:** La lógica de orquestación está definida y lista para ser activada.

### 2.5. Módulo `ui/api_config_dialog.py`
- **Función:** Proporciona una ventana de diálogo para que el usuario pueda introducir sus credenciales (claves de API) para Discogs y Spotify.
- **Estado:** La ventana está creada y es funcional, pero no hay un menú en la `MainWindow` para poder abrirla.

---

## 3. Otros Módulos Internos y Funcionalidades del Core

Estos son otros componentes clave del backend que proporcionan funcionalidades de soporte esenciales.

### 3.1. Módulo `core/audio_service.py`
- **Función:** El "cerebro" de la reproducción de audio, completamente desacoplado de la UI.
- **Capacidades:** Maneja el `QMediaPlayer`, controla los estados (play, pause, stop), gestiona el volumen y la posición, y delega tareas pesadas como el análisis de BPM a hilos secundarios.

### 3.2. Módulo `core/key_converter.py`
- **Función:** Utilidad para la gestión de tonos musicales.
- **Capacidades:** Convierte entre diferentes notaciones de tono, principalmente entre la notación estándar (ej. `F#m`) y el sistema Camelot (ej. `7A`), que es muy popular entre los DJs.

### 3.3. Módulo `core/threading.py`
- **Función:** Proporciona una clase `Worker` genérica para ejecutar cualquier función en un hilo de fondo.
- **Uso:** Se utiliza para operaciones que consumen tiempo, como el análisis de BPM, para evitar que la interfaz de usuario se congele y se mantenga siempre receptiva.

### 3.4. Módulo `core/database.py`
- **Función:** Gestiona todo lo relacionado con la base de datos SQLite.
- **Capacidades:**
    - Define el esquema de la base de datos (las tablas y sus columnas).
    - Proporciona funciones para inicializar la base de datos, crear conexiones y realizar operaciones CRUD (Crear, Leer, Actualizar, Borrar) sobre las pistas y playlists. 