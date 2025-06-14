import tkinter as tk
from tkinter import ttk

class StatusBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style="TFrame")
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            style="TLabel"
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=5)

    def set_status(self, message, clear_after_ms=0):
        """
        Muestra un mensaje en la barra de estado.
        
        Args:
            message (str): El mensaje a mostrar.
            clear_after_ms (int): Si es mayor que 0, el mensaje se borrará
                                  después de este número de milisegundos.
        """
        self.status_var.set(message)
        if clear_after_ms > 0:
            self.after(clear_after_ms, lambda: self.status_var.set("")) 