import tkinter as tk
from tkinter import ttk, filedialog, Menu
import threading
import queue

from core.metadata_reader import read_metadata
from core.database import init_db
from core.library_scanner import scan_directory
from ui.tracklist import Tracklist

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Biblioteca de Audio Inteligente")
        self.geometry("1200x800")

        self.scan_queue = queue.Queue()

        self.create_menu()
        self.create_main_widgets()
        self.create_status_bar()

        self.process_scan_queue()

    def create_menu(self):
        """Crea la barra de menú superior de la aplicación."""
        menubar = Menu(self)
        self.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Escanear Biblioteca...", command=self.scan_library)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

    def create_main_widgets(self):
        """Crea los widgets principales de la aplicación."""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tracklist = Tracklist(main_frame)
        self.tracklist.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tracklist.yview)
        self.tracklist.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Cargar datos al inicio
        self.tracklist.load_data()

    def create_status_bar(self):
        """Crea una barra de estado en la parte inferior de la ventana."""
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def scan_library(self):
        """Abre un diálogo para seleccionar una carpeta y la escanea."""
        directory_path = filedialog.askdirectory(
            title="Selecciona la carpeta de tu música"
        )
        if not directory_path:
            self.status_var.set("Escaneo cancelado.")
            return
        
        self.status_var.set(f"Escaneando: {directory_path}...")
        
        # Ejecutar el escaneo en un hilo separado para no bloquear la UI
        scan_thread = threading.Thread(
            target=scan_directory,
            args=(directory_path, self.scan_queue)
        )
        scan_thread.start()

    def process_scan_queue(self):
        """Procesa los mensajes de la cola del escáner y actualiza la UI."""
        try:
            message = self.scan_queue.get_nowait()
            if message == "scan_complete":
                self.status_var.set("Escaneo completado. Actualizando lista...")
                self.tracklist.load_data()
                self.status_var.set("Listo.")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_scan_queue)

if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
