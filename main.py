import tkinter as tk
from gui.app import MainApp
from database.connection import initialize_db

#HOLA
def main() -> None:
    """
    Función principal que inicializa la base de datos y la interfaz gráfica.
    """
    initialize_db()
    
    root: tk.Tk = tk.Tk()
    root.title("Almacen Unefista")
    root.geometry("1024x768")
    
    app: MainApp = MainApp(root)
    
    root.mainloop()
        
if __name__ == "__main__":
    main()