# 🎯 Plan de Mejoras Estratégicas para DjAlfin (Rama: Next)

Este documento detalla el plan de acción para mejorar la estabilidad, consistencia y mantenibilidad del proyecto DjAlfin.

---

### **Paso 1: Refactorización del Núcleo (Estabilidad Crítica)**

**Objetivo:** Crear un `backend` robusto, predecible y fácil de mantener.

*   **1.1. Unificar el Reproductor de Audio (`core/audio_player.py`):**
    *   **Problema:** Desconexión entre `main.py` y la API del reproductor, causando crashes (`AttributeError`).
    *   **Solución:** Refactorizar `AudioPlayer` en una clase cohesiva con una API clara: `play()`, `pause()`, `stop()`, `next()`, `previous()`, `set_volume()`, `get_progress()`.

*   **1.2. Fortalecer el Escáner de Biblioteca (`core/library_scanner.py`):**
    *   **Problema:** El escaneo puede fallar por completo si encuentra archivos corruptos.
    *   **Solución:** Implementar un manejo de errores robusto para que el escáner registre el error y continúe con el siguiente archivo.

---

### **Paso 2: Centralización de Estilos y Widgets (UI y DRY)**

**Objetivo:** Eliminar código repetido y garantizar una apariencia visual 100% consistente.

*   **2.1. Crear un Módulo de Widgets Personalizados (`ui/widgets.py`):**
    *   **Problema:** Componentes de UI definidos con estilos inconsistentes en múltiples archivos.
    *   **Solución:** Crear un nuevo archivo `ui/widgets.py` con widgets pre-estilizados (`StyledButton`, `HeaderLabel`, etc.) que usen el tema central.

*   **2.2. Forzar el Uso del Tema Central (`ui/theme.py`):**
    *   **Problema:** Estilos (colores, fuentes) "hardcodeados" en varios componentes de la UI.
    *   **Solución:** Realizar una búsqueda y reemplazo para usar siempre las variables del archivo `theme.py`.

---

### **Paso 3: Unificación de la Disposición y Flujo (UI/UX)**

**Objetivo:** Mejorar la organización del código de la interfaz y la distribución de los elementos en pantalla.

*   **3.1. Estandarizar el Método de Layout:**
    *   **Problema:** Uso mixto de `.pack()` y `.grid()`, complicando el diseño.
    *   **Solución:** Estandarizar el uso de `.grid()` para todos los paneles principales para un layout más predecible y flexible.

*   **3.2. Refactorizar `main.py` como Orquestador:**
    *   **Problema:** `main.py` tiene demasiada lógica que debería estar en componentes específicos.
    *   **Solución:** Simplificar `main.py` para que solo se encargue de inicializar y conectar los componentes del núcleo y la UI.

--- 