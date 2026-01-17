import tkinter as tk
from typing import Optional, Union
from gui.views.login import LoginView
from gui.views.inventario import InventarioView
from gui.views.movimientos import MovimientosView
from gui.views.envios import EnviosView
from gui.views.productos_salida import SalidasView

class MainApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        
        self.current_frame: Optional[tk.Widget] = None
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
    def __init__(self, parent: tk.Tk, controller: MainApp) -> None:
        super().__init__(parent)
        self.controller: MainApp = controller
        self.parent: tk.Tk = parent
        
        self.create_menu()
        
        
        self.view_container: tk.Frame = tk.Frame(self)
        self.view_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.show_view("Inventario")

    def create_menu(self) -> None:
        menubar: tk.Menu = tk.Menu(self.parent)
        self.parent.config(menu=menubar)

        modulos_menu: tk.Menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Módulos", menu=modulos_menu)
        modulos_menu.add_command(label="Inventario", command=lambda: self.show_view("Inventario"))
        modulos_menu.add_command(label="Movimientos (E/S)", command=lambda: self.show_view("Movimientos"))
        modulos_menu.add_command(label="Envios", command=lambda: self.show_view("Envios"))
        modulos_menu.add_command(label="Salidas", command=lambda: self.show_view("Salidas"))
        
        user_menu: tk.Menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sesión", menu=user_menu)
        user_menu.add_command(label="Cerrar Sesión", command=self.logout)

    def show_view(self, view_name: str) -> None:
        
        for widget in self.view_container.winfo_children():
            widget.destroy()
            
        if view_name == "Inventario":
            InventarioView(self.view_container).pack(fill="both", expand=True)
        elif view_name == "Movimientos":
            MovimientosView(self.view_container).pack(fill="both", expand=True)
        elif view_name == "Envios":
            EnviosView(self.view_container).pack(fill="both", expand=True)
        elif view_name == "Salidas":
            SalidasView(self.view_container).pack(fill="both", expand=True)

    def logout(self) -> None:
        self.parent.config(menu="") 
        self.controller.show_login()