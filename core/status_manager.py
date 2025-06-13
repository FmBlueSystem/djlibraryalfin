from typing import Any, Optional


class StatusManager:
    """
    Singleton para gestionar la barra de estado global de la aplicación.
    Permite a cualquier módulo actualizar el mensaje de estado.
    """

    _instance = None
    _status_widget: Optional[Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StatusManager, cls).__new__(cls)
        return cls._instance

    def set_status_widget(self, widget: Any):
        """
        Establece el widget de la GUI (por ejemplo, un tk.Label)
        que se usará como barra de estado.
        """
        self._status_widget = widget

    def set_status(self, message: str, duration_ms: int = 0):
        """
        Actualiza el mensaje en la barra de estado.

        Args:
            message (str): El texto a mostrar.
            duration_ms (int): Si es mayor que 0, el mensaje desaparecerá
                               después de esta cantidad de milisegundos.
        """
        if not self._status_widget:
            print(f"Status (UI no configurada): {message}")
            return

        self._status_widget.config(text=message)

        # Si se especifica una duración, programar que se borre
        if duration_ms > 0:
            self._status_widget.after(duration_ms, lambda: self.clear_status(message))

    def clear_status(self, message_to_clear: Optional[str] = None):
        """
        Limpia la barra de estado, opcionalmente solo si el mensaje actual
        coincide con el que se programó para borrar.
        """
        if self._status_widget:
            # Evita borrar un mensaje nuevo si el usuario hizo otra acción rápido
            if (
                message_to_clear is None
                or self._status_widget.cget("text") == message_to_clear
            ):
                self._status_widget.config(text="Listo")

    def get_status(self) -> str:
        """
        Obtiene el mensaje actual de la barra de estado.
        """
        if self._status_widget:
            return self._status_widget.cget("text")
        return ""
