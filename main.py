import tkinter as tk
from gui.app import MainApp
from database.connection import initialize_db

def main():
    # 1. Inicializar Base de Datos y tablas si no existen
    initialize_db()
    
    # 2. Configurar la ventana raíz
    root = tk.Tk()
    root.title("Sistema de Gestión de Almacén WMS")
    root.geometry("1024x768")
    
    # 3. Lanzar la aplicación principal
    app = MainApp(root)
    
    root.mainloop()

if __name__ == "__main__":
    main()