import tkinter as tk
from tkinter import ttk, filedialog, Menu, messagebox
import threading
import queue
import platform

from core.metadata_reader import read_metadata
from core.database import init_db
from core.library_scanner import scan_directory
from ui.tracklist import Tracklist
from ui.waveform_display import WaveformDisplay
from ui.theme_manager import theme_manager

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
        # Usar un PanedWindow para que el usuario pueda redimensionar las secciones
        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame superior para el tracklist
        tracklist_frame = ttk.Frame(main_pane, height=600)
        main_pane.add(tracklist_frame, weight=3)

        self.tracklist = Tracklist(tracklist_frame, self.update_waveform) # Pasamos la referencia a la función de callback
        self.tracklist.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tracklist_frame, orient="vertical", command=self.tracklist.yview)
        self.tracklist.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Frame inferior para la forma de onda
        waveform_frame = ttk.Frame(main_pane, height=200)
        main_pane.add(waveform_frame, weight=1)

        self.waveform_display = WaveformDisplay(waveform_frame)
        self.waveform_display.pack(fill="both", expand=True)

        # Cargar datos al inicio
        self.tracklist.load_data()

    def update_waveform(self, file_path):
        """Callback que se llama al seleccionar una pista para actualizar la forma de onda."""
        # Esto debería correr en un hilo para no bloquear la UI al generar la forma de onda
        from core.waveform_generator import generate_waveform_data
        
        def generator_thread():
            data = generate_waveform_data(file_path)
            # Pasamos los datos al widget de forma segura para la UI de Tkinter
            self.waveform_display.set_data(data)

        threading.Thread(target=generator_thread, daemon=True).start()

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
