# Registro de Tareas del Proyecto DjAlfin

Este archivo sirve como un registro temporal de las tareas de desarrollo mientras se soluciona la conectividad con Dart AI.

## Épica: Desarrollo del Núcleo de la Biblioteca v1

**ID Temporal:** EPIC-01
**Título:** [ÉPICA] Desarrollo del Núcleo de la Biblioteca v1
**Descripción:** Abarca el desarrollo inicial de la base de datos, el escáner de biblioteca y la interfaz de usuario principal para mostrar el listado de pistas.
**Estado:** **Completada**

---

### Sub-tareas de EPIC-01

1.  **ID Temporal:** CORE-DB
    **Título:** `[Core] Arquitectura de Base de Datos: Implementar SQLite`
    **Descripción:** Crear el módulo `core/database.py`. Definir e implementar el esquema de la tabla `tracks`. Proporcionar funciones para la conexión, inserción y consulta de pistas.
    **Dependencias:** Ninguna.
    **Estado:** **Completada**

2.  **ID Temporal:** CORE-SCAN
    **Título:** `[Core] Lógica de Escaneo: Implementar el Escáner de Biblioteca`
    **Descripción:** Crear el módulo `core/library_scanner.py`. Implementar la lógica para recorrer directorios, usar `metadata_reader` y guardar los datos en la base de datos SQLite.
    **Dependencias:** `CORE-DB`.
    **Estado:** **Completada**

3.  **ID Temporal:** UI-LIST
    **Título:** `[UI] Interfaz de Usuario: Implementar la Vista de Biblioteca (Tracklist)`
    **Descripción:** Rediseñar la ventana principal para incluir un `ttk.Treeview`. Conectar la UI a la base de datos para mostrar las pistas de la biblioteca al iniciar la aplicación.
    **Dependencias:** `CORE-DB`.
    **Estado:** **Completada**

---

## Épica: Edición de Metadatos en la Aplicación v1

**ID Temporal:** EPIC-02
**Título:** [ÉPICA] Edición de Metadatos en la Aplicación v1
**Descripción:** Permitir al usuario editar los metadatos de las pistas directamente desde la interfaz de la aplicación.
**Estado:** **Completada**

---

### Sub-tareas de EPIC-02

1.  **ID Temporal:** UI-EDIT
    **Título:** `[UI] Implementar Edición en la Celda del Tracklist`
    **Descripción:** Permitir al usuario hacer doble clic en una celda del `Tracklist`, que aparezca un campo de texto para editar, y que se capture el nuevo valor al presionar Enter o al perder el foco.
    **Dependencias:** Ninguna.
    **Estado:** **Completada**

2.  **ID Temporal:** CORE-WRITE
    **Título:** `[Core] Crear Módulo Escritor de Metadatos`
    **Descripción:** Crear `core/metadata_writer.py` con una función que pueda modificar los tags de metadatos de los archivos de audio usando `mutagen`.
    **Dependencias:** `UI-EDIT`.
    **Estado:** **Completada**

3.  **ID Temporal:** CORE-DB-UPDATE
    **Título:** `[Core] Actualizar Base de Datos en Edición`
    **Descripción:** Añadir una función en `core/database.py` para actualizar un campo específico de una pista en la base de datos.
    **Dependencias:** `UI-EDIT`.
    **Estado:** **Completada**

4.  **ID Temporal:** INT-EDIT
    **Título:** `[Integración] Conectar UI con Backend de Edición`
    **Descripción:** Unir el evento de edición de la UI con el `metadata_writer` y la actualización de la base de datos para hacer la edición persistente.
    **Dependencias:** `CORE-WRITE`, `CORE-DB-UPDATE`.
    **Estado:** **Completada** 