import tkinter as tk
from typing import List, Any


class WaveformDisplay(tk.Canvas):
    def __init__(self, master: tk.Widget, **kwargs: Any) -> None:
        # Un color de fondo oscuro es típico para las formas de onda
        super().__init__(master, bg="#2B2B2B", **kwargs)
        self.waveform_data: List[float] = []
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event: tk.Event) -> None:
        """Se redibuja la forma de onda cuando el widget cambia de tamaño."""
        self.draw_waveform()

    def set_data(self, data: List[float]) -> None:
        """
        Establece los datos de la forma de onda y la redibuja.

        Args:
            data (list): Una lista de puntos de datos normalizados (0.0 a 1.0).
        """
        self.waveform_data = data
        self.draw_waveform()

    def draw_waveform(self) -> None:
        """Dibuja los datos de la forma de onda en el canvas."""
        self.delete("all")  # Limpiar el canvas

        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

        # Si no hay datos, no podemos dividir por cero
        if not self.waveform_data:
            return

        # El ancho de cada barra de la forma de onda
        bar_width = canvas_width / len(self.waveform_data)

        y_center = canvas_height / 2
        # La altura máxima de la barra es la mitad de la altura del canvas, con margen
        max_bar_height = (canvas_height / 2) * 0.95

        for i, point in enumerate(self.waveform_data):
            x0 = i * bar_width

            # La altura de la barra es proporcional al punto de datos
            bar_height = point * max_bar_height

            # Dibujar solo la mitad superior de la forma de onda
            # y0 es la coordenada superior, y1 la inferior (el centro)
            y0 = y_center - bar_height
            y1 = y_center
            x1 = x0 + bar_width

            self.create_rectangle(x0, y0, x1, y1, fill="#4682B4", outline="")
