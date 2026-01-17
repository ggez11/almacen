import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Optional, Dict

from services.auth_service import login

class LoginView(tk.Frame):
    def __init__(self, parent: tk.Widget, controller: Any) -> None:
        super().__init__(parent)
        self.controller: Any = controller
        
        # --- CONFIGURACIÓN DE COLORES ---
        self.color_bg: str = "#F3F4F6"
        self.color_card: str = "#FFFFFF"
        self.color_header: str = "#111827"
        self.color_accent: str = "#0F766E"
        self.color_text_gray: str = "#6B7280"
        self.color_border: str = "#E5E7EB"
        
        self.configure(bg=self.color_bg)
        
        # --- TARJETA CENTRAL ---
        self.card: tk.Frame = tk.Frame(self, bg=self.color_card, bd=0)
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=580)
        
        shadow: tk.Frame = tk.Frame(self, bg="#D1D5DB")
        shadow.place(relx=0.5, rely=0.5, anchor="center", width=402, height=582)
        self.card.lift()

        # Atributos de widgets que se inicializan en los métodos internos
        self.role_combo: Optional[ttk.Combobox] = None
        self.user_entry: Optional[tk.Entry] = None
        self.pass_entry: Optional[tk.Entry] = None
        self.var_remember: tk.IntVar = tk.IntVar()
        self.btn_eye: Optional[tk.Label] = None

        # Renderizar partes
        self._dibujar_header()
        self._dibujar_body()
        self._dibujar_footer()

    def _dibujar_header(self) -> None:
        """Parte superior oscura con el logo y título"""
        header_frame: tk.Frame = tk.Frame(self.card, bg=self.color_header, height=150)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        icon_bg: tk.Label = tk.Label(header_frame, text="🏠", font=("Arial", 24), 
                                   bg="#0D9488", fg="white", width=3, height=1)
        icon_bg.pack(pady=(30, 10))

        tk.Label(header_frame, text="LogiStock Pro", 
                 font=("Segoe UI", 16, "bold"), 
                 bg=self.color_header, fg="white").pack()
        
        tk.Label(header_frame, text="WMS PORTAL ACCESS", 
                 font=("Segoe UI", 8, "bold"), 
                 bg=self.color_header, fg="#2DD4BF").pack()

    def _dibujar_body(self) -> None:
        """Formulario de ingreso"""
        body_frame: tk.Frame = tk.Frame(self.card, bg=self.color_card, padx=30, pady=20)
        body_frame.pack(fill="both", expand=True)

        tk.Label(body_frame, text="SELECCIONAR ROL", 
                 font=("Arial", 8, "bold"), fg=self.color_text_gray, bg=self.color_card, anchor="w").pack(fill="x", pady=(10, 5))
        
        self.role_combo = ttk.Combobox(body_frame, values=["Almacenero", "Administrador", "Consultor"], state="readonly")
        self.role_combo.current(0)
        self.role_combo.pack(fill="x", pady=(0, 15), ipady=3)

        tk.Label(body_frame, text="CREDENCIALES", 
                 font=("Arial", 7), fg="#9CA3AF", bg=self.color_card).pack(pady=(5, 10))

        # Inputs modernos (Retornan tk.Entry)
        self.user_entry = self._crear_input_moderno(body_frame, "👤", "Usuario o ID", is_password=False)
        self.pass_entry = self._crear_input_moderno(body_frame, "🔒", "Contraseña", is_password=True)

        opts_frame: tk.Frame = tk.Frame(body_frame, bg=self.color_card)
        opts_frame.pack(fill="x", pady=(10, 20))
        
        chk: tk.Checkbutton = tk.Checkbutton(opts_frame, text="Recordar ID", variable=self.var_remember, 
                                            bg=self.color_card, fg=self.color_text_gray, activebackground=self.color_card,
                                            font=("Arial", 9), relief="flat", highlightthickness=0)
        chk.pack(side="left")

        btn_forgot: tk.Label = tk.Label(opts_frame, text="¿Olvidó su clave?", 
                                      bg=self.color_card, fg=self.color_accent, font=("Arial", 9, "bold"), cursor="hand2")
        btn_forgot.pack(side="right")

        self.btn_login: tk.Button = tk.Button(body_frame, text="Ingreso Seguro  ➜", command=self.verificar,
                                           bg=self.color_accent, fg="white", 
                                           font=("Segoe UI", 11, "bold"), 
                                           relief="flat", cursor="hand2", pady=8)
        self.btn_login.pack(fill="x")

    def _dibujar_footer(self) -> None:
        footer_frame: tk.Frame = tk.Frame(self.card, bg="#F9FAFB", height=40)
        footer_frame.pack(fill="x", side="bottom")
        
        tk.Label(footer_frame, text="● Sistema Online", fg="#10B981", bg="#F9FAFB", font=("Arial", 8)).pack(side="left", padx=20, pady=10)
        tk.Label(footer_frame, text="Ayuda & Soporte", fg=self.color_text_gray, bg="#F9FAFB", font=("Arial", 8)).pack(side="right", padx=20, pady=10)

    def _crear_input_moderno(self, parent: tk.Widget, icon_char: str, placeholder: str, is_password: bool = False) -> tk.Entry:
        """Crea un campo de texto estilizado y retorna el widget Entry"""
        container: tk.Frame = tk.Frame(parent, bg="white", highlightbackground=self.color_border, highlightthickness=1, bd=0)
        container.pack(fill="x", pady=5, ipady=5)

        lbl_icon: tk.Label = tk.Label(container, text=icon_char, bg="white", fg=self.color_text_gray, font=("Arial", 12))
        lbl_icon.pack(side="left", padx=(10, 5))

        entry: tk.Entry = tk.Entry(container, bg="white", bd=0, font=("Segoe UI", 10), fg="#374151", highlightthickness=0)
        entry.pack(side="left", fill="x", expand=True)
        
        entry.insert(0, placeholder)
        # Usamos lambda e: para capturar el evento de Tkinter (tk.Event)
        entry.bind("<FocusIn>", lambda e: self._on_entry_focus(entry, placeholder, is_password))
        entry.bind("<FocusOut>", lambda e: self._on_entry_blur(entry, placeholder, is_password))
        
        if is_password:
            self.btn_eye = tk.Label(container, text="👁", bg="white", fg=self.color_text_gray, cursor="hand2")
            self.btn_eye.pack(side="right", padx=10)
            self.btn_eye.bind("<Button-1>", lambda e: self._toggle_password(entry))
        
        return entry

    def _on_entry_focus(self, entry: tk.Entry, placeholder: str, is_password: bool) -> None:
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(fg="black")
            if is_password:
                entry.config(show="*")

    def _on_entry_blur(self, entry: tk.Entry, placeholder: str, is_password: bool) -> None:
        if entry.get() == "":
            entry.insert(0, placeholder)
            entry.config(fg=self.color_text_gray)
            if is_password:
                entry.config(show="")

    def _toggle_password(self, entry: tk.Entry) -> None:
        if entry.get() == "Contraseña": return
        if not self.btn_eye: return

        current_show: str = entry.cget('show')
        if current_show == "*":
            entry.config(show="")
            self.btn_eye.config(fg=self.color_accent)
        else:
            entry.config(show="*")
            self.btn_eye.config(fg=self.color_text_gray)

    def verificar(self) -> None:
        # Verificación de existencia de widgets para evitar errores de Optional
        if not self.user_entry or not self.pass_entry: return

        user: str = self.user_entry.get()
        password: str = self.pass_entry.get()
        
        if user == "Usuario o ID" or password == "Contraseña":
            messagebox.showwarning("Datos incompletos", "Por favor ingrese usuario y contraseña")
            return

        if login(user, password):
            self.controller.show_main_system()
        else:
            messagebox.showerror("Error de Acceso", "Credenciales incorrectas.\nIntente: admin / admin")