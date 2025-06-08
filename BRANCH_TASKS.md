# Tareas y Retos de la Rama `feature/smart-playlists`

Este documento resume los objetivos de la rama actual y los inconvenientes técnicos encontrados durante el desarrollo.

## Objetivos de la Rama

1.  **Implementar Controles de Navegación (Siguiente/Anterior):**
    *   Añadir botones "⏮ Prev" y "Next ⏭" al panel de reproducción.
    *   Implementar la lógica para que estos botones seleccionen y reproduzcan la canción anterior o siguiente en la lista de reproducción.
    *   Añadir funcionalidad de auto-play para que la siguiente canción se reproduzca automáticamente al terminar la actual.

2.  **Refactorización Profunda del Código Base:**
    *   **Base de Datos (`core/database.py`):** Migrar de funciones procedurales a una clase `DatabaseManager` para encapsular toda la lógica de la base de datos y facilitar su gestión.
    *   **Escáner de Biblioteca (`core/library_scanner.py`):** Convertir el script de escaneo en una clase `LibraryScanner` que colabore con `DatabaseManager`.
    *   **Lista de Pistas (`ui/tracklist.py`):** Refactorizar el componente para que sea un `ttk.Frame` que *contiene* un `Treeview`, en lugar de heredar de él. Esto mejora la composición y reduce la complejidad.
    *   **Aplicación Principal (`main.py`):** Reestructurar la clase principal de la aplicación para que orqueste los nuevos componentes refactorizados, simplificando la lógica de reproducción y el manejo de estado.

## Inconvenientes y Bloqueos

Durante la refactorización, me he encontrado con varios problemas significativos:

1.  **Errores de Importación Persistentes:** Tras convertir `core/database.py` en una clase, el archivo `ui/tracklist.py` seguía intentando importar funciones que ya no existían, causando un `ImportError`. A pesar de múltiples intentos, las herramientas de edición de código no lograron eliminar la línea de importación conflictiva, lo que requirió varios reintentos y enfoques alternativos hasta que finalmente se solucionó (aparentemente de forma externa).

2.  **Fallos en la Aplicación de Cambios:** En varias ocasiones, especialmente durante la reescritura de `main.py` y `ui/tracklist.py`, la herramienta para aplicar los cambios en el código generó un resultado incorrecto, mezclando código antiguo y nuevo de forma incoherente. Esto "rompió" los archivos y me obligó a leerlos de nuevo y reemplazarlos por completo, lo que retrasó el progreso.

3.  **Error de Atributo en `AudioPlayer` (Problema Actual):** La aplicación ahora se inicia pero crashea inmediatamente al intentar reproducir una canción. El error es un `AttributeError`, lo que significa que `main.py` está llamando a métodos en la clase `AudioPlayer` (como `play_audio`, `stop_audio`) que no existen con ese nombre. Mi refactorización no se propagó correctamente a `core/audio_player.py`, y ahora debo alinear la interfaz de esa clase con el resto de la aplicación. 