import tkinter as tk
from tkinter import messagebox
from services.auth_service import login

class LoginView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        frame = tk.Frame(self)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="SISTEMA ALMACEN", font=("Arial", 20, "bold")).pack(pady=20)

        tk.Label(frame, text="Usuario:").pack()
        self.user_entry = tk.Entry(frame)
        self.user_entry.pack(pady=5)

        tk.Label(frame, text="Contraseña:").pack()
        self.pass_entry = tk.Entry(frame, show="*")
        self.pass_entry.pack(pady=5)

        tk.Button(frame, text="Ingresar", command=self.verificar, bg="#158645", fg="white").pack(pady=20, fill="x")
        
        # Nota para el usuario
        tk.Label(frame, text="Default: admin / admin", fg="gray").pack()

    def verificar(self):
        user = self.user_entry.get()
        password = self.pass_entry.get()
        
        if login(user, password):
            self.controller.show_main_system()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")