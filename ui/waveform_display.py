import tkinter as tk

class WaveformDisplay(tk.Canvas):
    def __init__(self, master, **kwargs):
        # Un color de fondo oscuro es típico para las formas de onda
        super().__init__(master, bg='#2B2B2B', **kwargs)
        self.waveform_data = []
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Se redibuja la forma de onda cuando el widget cambia de tamaño."""
        self.draw_waveform()

    def set_data(self, data):
        """
        Establece los datos de la forma de onda y la redibuja.

        Args:
            data (list): Una lista de puntos de datos normalizados (0.0 a 1.0).
        """
        self.waveform_data = data
        self.draw_waveform()

    def draw_waveform(self):
        """Dibuja los datos de la forma de onda en el canvas."""
        self.delete("all")  # Limpiar el canvas
        if not self.waveform_data:
            return

        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        # El ancho de cada barra de la forma de onda
        bar_width = canvas_width / len(self.waveform_data)
        
        for i, point in enumerate(self.waveform_data):
            x0 = i * bar_width
            y0_center = canvas_height / 2
            
            # La altura de la barra es proporcional al punto de datos
            bar_height = point * (canvas_height * 0.9) # Usar 90% de la altura para margen
            
            # Dibujar la barra desde el centro hacia arriba y hacia abajo
            y0 = y0_center - bar_height / 2
            y1 = y0_center + bar_height / 2
            x1 = x0 + bar_width

            self.create_rectangle(x0, y0, x1, y1, fill='#4682B4', outline="") 