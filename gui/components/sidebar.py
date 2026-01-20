# gui/components/sidebar.py (VERSIÓN ACTUALIZADA)
import tkinter as tk
from typing import Dict, List, Tuple, Any, Callable

# Colores compartidos para el Sidebar
SIDEBAR_COLORS: Dict[str, str] = {
    "bg": "#FFFFFF",           # Fondo blanco limpio
    "text": "#6B7280",         # Gris texto
    "text_active": "#0F172A",  # Negro suave para activo
    "hover": "#F3F4F6",        # Gris muy claro
    "active_bg": "#F0FDFA",    # Fondo activo (Teal muy claro)
    "active_border": "#0D9488" # Borde activo (Teal principal)
}

class Sidebar(tk.Frame):
    def __init__(self, parent: tk.Widget, controller: Any) -> None:
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=SIDEBAR_COLORS["bg"], width=250)
        self.pack_propagate(False) # Forzar ancho fijo

        # Almacén de referencias a los botones para cambiar estilos
        self.menu_buttons: Dict[str, tk.Widget] = {}

        self._construir_logo()
        self._construir_menu()
        self._construir_perfil()

    def _construir_logo(self) -> None:
        logo_frame: tk.Frame = tk.Frame(self, bg=SIDEBAR_COLORS["bg"], pady=30)
        logo_frame.pack(fill="x")
        
        tk.Label(logo_frame, text="📦 Almacen", font=("Segoe UI", 16, "bold"), 
                 bg=SIDEBAR_COLORS["bg"], fg="#111827").pack()

    def _construir_menu(self) -> None:
        menu_container: tk.Frame = tk.Frame(self, bg=SIDEBAR_COLORS["bg"])
        menu_container.pack(fill="both", expand=True, pady=10)

        # Definición del Menú: (Texto, ViewKey, Icono)
        # ViewKey debe coincidir con los nombres en app.py -> show_view()
        opciones: List[Tuple[str, str, str]] = [
            ("Inventario", "Inventario", "📦"),
            ("  Movimientos", "Movimientos", "⇆"),
            ("Envios", "Envios", "🛒"),
            ("Salidas", "Salidas", "📉"),
            ("---", "---", "---"),  # Separador
        ]

        for text, key, icon in opciones:
            if text == "---":  # Separador
                self._crear_separador(menu_container)
            else:
                self._crear_boton_menu(menu_container, text, key, icon)

    def _crear_separador(self, parent: tk.Frame) -> None:
        """Crea un separador visual en el menú."""
        separator = tk.Frame(parent, bg="#E5E7EB", height=1)
        separator.pack(fill="x", pady=10, padx=10)

    def _crear_boton_menu(self, parent: tk.Frame, text: str, key: str, icon: str) -> None:
        btn_frame: tk.Frame = tk.Frame(parent, bg=SIDEBAR_COLORS["bg"], height=50, cursor="hand2")
        btn_frame.pack(fill="x", pady=2, padx=10)
        btn_frame.pack_propagate(False)

        # Barra lateral indicadora (invisible por defecto)
        indicator: tk.Frame = tk.Frame(btn_frame, bg=SIDEBAR_COLORS["bg"], width=4)
        indicator.pack(side="left", fill="y")

        lbl_icon: tk.Label = tk.Label(btn_frame, text=icon, font=("Arial", 14), 
                                      bg=SIDEBAR_COLORS["bg"], fg=SIDEBAR_COLORS["text"])
        lbl_icon.pack(side="left", padx=(15, 10))
        
        lbl_text: tk.Label = tk.Label(btn_frame, text=text, font=("Segoe UI", 10, "bold"), 
                                      bg=SIDEBAR_COLORS["bg"], fg=SIDEBAR_COLORS["text"])
        lbl_text.pack(side="left")

        # Eventos
        # Usamos lambda con argumentos por defecto para capturar el valor actual de key
        click_handler = lambda e, k=key: self.controller.show_view(k)
        
        for w in [btn_frame, lbl_icon, lbl_text]:
            w.bind("<Button-1>", click_handler)

        # Guardamos referencias para manipular estilos luego
        self.menu_buttons[key] = {
            "frame": btn_frame,
            "indicator": indicator,
            "icon": lbl_icon,
            "text": lbl_text
        }

    def _construir_perfil(self) -> None:
        user_frame: tk.Frame = tk.Frame(self, bg=SIDEBAR_COLORS["bg"], pady=20, padx=20)
        user_frame.pack(side="bottom", fill="x")
        
        # Separador
        tk.Frame(user_frame, bg="#E5E7EB", height=1).pack(fill="x", pady=(0, 15))

        row: tk.Frame = tk.Frame(user_frame, bg=SIDEBAR_COLORS["bg"])
        row.pack(fill="x")
        
        tk.Label(row, text="👤", font=("Arial", 20), bg=SIDEBAR_COLORS["bg"]).pack(side="left")
        
        info: tk.Frame = tk.Frame(row, bg=SIDEBAR_COLORS["bg"], padx=10)
        info.pack(side="left")
        tk.Label(info, text="Admin Usuario", font=("Segoe UI", 9, "bold"), bg=SIDEBAR_COLORS["bg"]).pack(anchor="w")
        
        # Botón Logout
        logout_btn = tk.Label(row, text="🚪", font=("Arial", 12), bg=SIDEBAR_COLORS["bg"], 
                 fg="red", cursor="hand2")
        logout_btn.pack(side="right")
        logout_btn.bind("<Button-1>", lambda e: self.controller.logout())

    def set_active(self, view_key: str) -> None:
        """Resalta el botón de la vista actual y apaga los demás."""
        for key, widgets in self.menu_buttons.items():
            is_active = (key == view_key)
            
            bg_color = SIDEBAR_COLORS["active_bg"] if is_active else SIDEBAR_COLORS["bg"]
            fg_color = SIDEBAR_COLORS["text_active"] if is_active else SIDEBAR_COLORS["text"]
            bar_color = SIDEBAR_COLORS["active_border"] if is_active else SIDEBAR_COLORS["bg"]

            widgets["frame"].configure(bg=bg_color)
            widgets["indicator"].configure(bg=bar_color)
            widgets["icon"].configure(bg=bg_color, fg=fg_color)
            widgets["text"].configure(bg=bg_color, fg=fg_color)