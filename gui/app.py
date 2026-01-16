import tkinter as tk
from gui.views.login import LoginView
from gui.views.inventario import InventarioView
from gui.views.movimientos import MovimientosView

class MainApp:
    def __init__(self, root):
        self.root = root
        self.current_frame = None
        self.show_login()

    def show_login(self):
        if self.current_frame:
            self.current_frame.destroy()
        # Pasamos self para que el login pueda llamar a show_main_system
        self.current_frame = LoginView(self.root, self)
        self.current_frame.pack(fill="both", expand=True)

    def show_main_system(self):
        if self.current_frame:
            self.current_frame.destroy()
        
        # Crear contenedor principal con Menu y Vistas
        self.current_frame = MainSystem(self.root, self)
        self.current_frame.pack(fill="both", expand=True)

class MainSystem(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        
        self.create_menu()
        
        # Contenedor para las vistas cambiantes
        self.view_container = tk.Frame(self)
        self.view_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cargar vista por defecto
        self.show_view("Inventario")

    def create_menu(self):
        menubar = tk.Menu(self.parent)
        self.parent.config(menu=menubar)

        modulos_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Módulos", menu=modulos_menu)
        modulos_menu.add_command(label="Inventario", command=lambda: self.show_view("Inventario"))
        modulos_menu.add_command(label="Movimientos (E/S)", command=lambda: self.show_view("Movimientos"))
        
        user_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sesión", menu=user_menu)
        user_menu.add_command(label="Cerrar Sesión", command=self.logout)

    def show_view(self, view_name):
        # Limpiar contenedor
        for widget in self.view_container.winfo_children():
            widget.destroy()
            
        if view_name == "Inventario":
            InventarioView(self.view_container).pack(fill="both", expand=True)
        elif view_name == "Movimientos":
            MovimientosView(self.view_container).pack(fill="both", expand=True)

    def logout(self):
        self.parent.config(menu="") # Limpiar menu
        self.controller.show_login()