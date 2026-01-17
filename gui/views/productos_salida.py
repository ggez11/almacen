import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Union

# Importaciones del sistema
from database.queries import get_all_products
from gui.components.widgets import EntryWithPlaceholder

# --- CONFIGURACIÓN DE ESTILOS (Tema Naranja - Ajustes) ---
COLORS: Dict[str, str] = {
    "bg_main": "#FFF7ED",       # Naranja muy claro
    "bg_sidebar": "#FFFFFF",
    "primary": "#F97316",       # Naranja alerta
    "primary_dark": "#C2410C",
    "text_dark": "#431407",
    "text_gray": "#9A3412",
    "border": "#FFEDD5",
    "white": "#FFFFFF",
    "danger": "#EF4444"
}

class SalidasView(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])

        # Lista de manifiesto (items a sacar)
        self.manifest_items: List[Dict[str, Any]] = []

        # Estructura Principal
        self.main_area: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.main_area.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.sidebar: tk.Frame = tk.Frame(self, bg=COLORS["white"], width=320, 
                                          highlightbackground=COLORS["border"], highlightthickness=1)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        self._construir_area_principal()
        self._construir_sidebar_manifiesto()
        self.cargar_productos_grid()

    def _construir_area_principal(self) -> None:
        # Header
        tk.Label(self.main_area, text="Gestión de Inventario / Salidas Especiales", 
                 font=("Segoe UI", 9), fg=COLORS["primary"], bg=COLORS["bg_main"]).pack(anchor="w")
        
        tk.Label(self.main_area, text="Ajustes y Mermas", font=("Segoe UI", 20, "bold"), 
                 fg=COLORS["text_dark"], bg=COLORS["bg_main"]).pack(anchor="w")

        # Buscador
        search_fr: tk.Frame = tk.Frame(self.main_area, bg="white", padx=10, pady=5, 
                                       highlightthickness=1, highlightbackground=COLORS["border"])
        search_fr.pack(fill="x", pady=20)
        
        self.entry_search: EntryWithPlaceholder = EntryWithPlaceholder(
            search_fr, placeholder="Escanear producto para añadir...", bg="white", bd=0
        )
        self.entry_search.pack(fill="x")

        # Grid Canvas (Para tarjetas de productos)
        self.canvas_grid = tk.Canvas(self.main_area, bg=COLORS["bg_main"], highlightthickness=0)
        self.frame_grid = tk.Frame(self.canvas_grid, bg=COLORS["bg_main"])
        
        self.scroll_grid = ttk.Scrollbar(self.main_area, orient="vertical", command=self.canvas_grid.yview)
        
        self.canvas_grid.create_window((0, 0), window=self.frame_grid, anchor="nw")
        self.canvas_grid.configure(yscrollcommand=self.scroll_grid.set)
        
        self.frame_grid.bind("<Configure>", lambda e: self.canvas_grid.configure(scrollregion=self.canvas_grid.bbox("all")))

        self.canvas_grid.pack(side="left", fill="both", expand=True)
        self.scroll_grid.pack(side="right", fill="y")

    def _construir_sidebar_manifiesto(self) -> None:
        # Header Manifiesto
        head: tk.Frame = tk.Frame(self.sidebar, bg="white", pady=20)
        head.pack(fill="x")
        
        tk.Label(head, text="TOTAL UNIDADES A RETIRAR", font=("Segoe UI", 8), fg=COLORS["text_gray"], bg="white").pack()
        self.lbl_total_count: tk.Label = tk.Label(head, text="0", font=("Segoe UI", 36, "bold"), 
                                                  fg=COLORS["primary"], bg="white")
        self.lbl_total_count.pack()

        tk.Frame(self.sidebar, bg=COLORS["border"], height=1).pack(fill="x", padx=20)

        # Scroll de items seleccionados
        self.items_container: tk.Frame = tk.Frame(self.sidebar, bg="white")
        self.items_container.pack(fill="both", expand=True, padx=15, pady=10)

        # Footer Actions
        footer: tk.Frame = tk.Frame(self.sidebar, bg="white", padx=20, pady=20)
        footer.pack(side="bottom", fill="x")

        warn: tk.Frame = tk.Frame(footer, bg="#FEF2F2", padx=10, pady=10)
        warn.pack(fill="x", pady=(0, 10))
        tk.Label(warn, text="⚠ Esta acción descuenta inventario inmediatamente.", 
                 font=("Segoe UI", 8), fg=COLORS["danger"], bg="#FEF2F2", justify="left").pack()

        tk.Button(footer, text="REGISTRAR AJUSTE", bg=COLORS["primary"], fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=10, cursor="hand2",
                  command=self.registrar_ajuste).pack(fill="x")

    def cargar_productos_grid(self) -> None:
        for w in self.frame_grid.winfo_children(): w.destroy()

        try:
            productos = get_all_products()
        except:
            productos = []

        # Crear Grid (Layout manual simple con pack y frames)
        # Para un grid real flexible en Tkinter, usamos grid() con contadores
        row_frame: Union[tk.Frame, None] = None
        
        for i, p in enumerate(productos):
            if i % 3 == 0: # 3 columnas
                row_frame = tk.Frame(self.frame_grid, bg=COLORS["bg_main"])
                row_frame.pack(fill="x", pady=10)
            
            if row_frame:
                self._crear_tarjeta_producto(row_frame, p[1], p[2], p[4], p[5])

    def _crear_tarjeta_producto(self, parent: tk.Frame, name: str, sku: str, stock: int, loc: str) -> None:
        card: tk.Frame = tk.Frame(parent, bg="white", padx=10, pady=10, width=180, height=150,
                                  highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(side="left", padx=10)
        card.pack_propagate(False) # Mantener tamaño fijo

        tk.Label(card, text=f"{stock} Unids", bg="#DCFCE7", fg="#166534", font=("Segoe UI", 8)).pack(anchor="e")
        tk.Label(card, text=name, font=("Segoe UI", 9, "bold"), bg="white", wraplength=160).pack(anchor="w", pady=5)
        tk.Label(card, text=f"SKU: {sku}", font=("Segoe UI", 8), fg=COLORS["text_gray"], bg="white").pack(anchor="w")
        
        tk.Button(card, text="+ Agregar", bg=COLORS["bg_main"], fg=COLORS["primary"], relief="flat",
                  command=lambda: self.agregar_al_manifiesto(name, sku)).pack(side="bottom", fill="x")

    def agregar_al_manifiesto(self, name: str, sku: str) -> None:
        self.manifest_items.append({"name": name, "sku": sku, "reason": "Merma"})
        self._renderizar_manifiesto()

    def _renderizar_manifiesto(self) -> None:
        for w in self.items_container.winfo_children(): w.destroy()
        
        self.lbl_total_count.config(text=str(len(self.manifest_items)))

        for item in self.manifest_items:
            fr: tk.Frame = tk.Frame(self.items_container, bg="white", pady=5, highlightbackground=COLORS["border"], highlightthickness=1)
            fr.pack(fill="x", pady=2)
            
            tk.Label(fr, text=item['name'], font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w", padx=5)
            
            opts: tk.Frame = tk.Frame(fr, bg="white")
            opts.pack(fill="x", padx=5)
            
            ttk.Combobox(opts, values=["Dañado", "Vencido", "Robo", "Uso Interno"], width=15).pack(side="left")
            tk.Button(opts, text="X", bg="white", fg="red", bd=0, width=2).pack(side="right")

    def registrar_ajuste(self) -> None:
        if not self.manifest_items: return
        messagebox.showinfo("Registro", "Ajuste de inventario registrado.")
        self.manifest_items.clear()
        self._renderizar_manifiesto()