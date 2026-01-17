import tkinter as tk
from typing import Optional

# Importaciones de vistas y componentes
from gui.components.sidebar import Sidebar
from gui.views.login import LoginView
from gui.views.inventario import InventarioView
from gui.views.movimientos import MovimientosView
from gui.views.envios import EnviosView
from gui.views.productos_salida import SalidasView 

class MainApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.current_frame: Optional[tk.Widget] = None
        
        self.root.geometry("1280x720")
        self.root.title("Nexus WMS")
        
        self.show_login()

    def show_login(self) -> None:
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = LoginView(self.root, self)
        self.current_frame.pack(fill="both", expand=True)

    def show_main_system(self) -> None:
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = MainSystem(self.root, self)
        self.current_frame.pack(fill="both", expand=True)

class MainSystem(tk.Frame):
    def __init__(self, parent: tk.Widget, controller: MainApp) -> None:
        super().__init__(parent)
        self.controller = controller
        
        # Configuración del Layout Principal: Sidebar (Izq) | Contenido (Der)
        self.sidebar: Sidebar = Sidebar(self, controller=self)
        self.sidebar.pack(side="left", fill="y")
        
        # Contenedor para las Vistas
        self.view_container: tk.Frame = tk.Frame(self, bg="#F3F4F6")
        self.view_container.pack(side="right", fill="both", expand=True)
        
        # Cargar vista por defecto
        self.show_view("Inventario")

    def show_view(self, view_name: str) -> None:
        """Cambia la vista central y actualiza el sidebar."""
        
        # 1. Limpiar contenedor
        for widget in self.view_container.winfo_children():
            widget.destroy()
            
        # 2. Instanciar nueva vista
        if view_name == "Inventario":
            # Nota: InventarioView ya NO debe tener su sidebar interno
            view = InventarioView(self.view_container)
        elif view_name == "Movimientos":
            view = MovimientosView(self.view_container)
        elif view_name == "Envios":
            view = EnviosView(self.view_container)
        elif view_name == "Salidas":
            view = SalidasView(self.view_container)
        else:
            return

        view.pack(fill="both", expand=True)
        
        # 3. Actualizar estado visual del sidebar
        self.sidebar.set_active(view_name)

    def logout(self) -> None:
        self.controller.show_login()