import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from typing import Dict, List, Tuple, Any, Optional, Union

# Importaciones locales
from database.queries import get_all_products, insert_product
from ..widgets import EntryWithPlaceholder

# --- CONFIGURACIÓN DE COLORES Y ESTILOS ---
# Usamos un diccionario con tipos definidos para los colores
COLORS: Dict[str, str] = {
    "bg_main": "#F3F4F6",
    "bg_sidebar": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "primary": "#0D9488",
    "primary_light": "#E0F2F1",
    "text_dark": "#111827",
    "text_gray": "#6B7280",
    "border": "#E5E7EB",
    "success_bg": "#D1FAE5", "success_fg": "#065F46",
    "warning_bg": "#FEF3C7", "warning_fg": "#92400E",
    "info_bg": "#DBEAFE",    "info_fg": "#1E40AF"
}

# Definición de tipos para fuentes (Tuplas de 3 elementos)
FontTuple = Tuple[str, int, str]
FONT_H1: FontTuple = ("Segoe UI", 18, "bold")
FONT_H2: FontTuple = ("Segoe UI", 12, "bold")
FONT_BODY: Tuple[str, int] = ("Segoe UI", 10)
FONT_SMALL: Tuple[str, int] = ("Segoe UI", 9)

class InventarioView(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])

        # Atributos de instancia tipados
        self.sidebar: tk.Frame = tk.Frame(self, bg=COLORS["bg_sidebar"], width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_area: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.main_area.pack(side="right", fill="both", expand=True)

        # Atributos para el área de scroll
        self.canvas: Optional[tk.Canvas] = None
        self.scrollable_frame: Optional[tk.Frame] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None

        # Construir UI
        self._construir_sidebar()
        self._construir_topbar()
        self._construir_lista_productos()

    def _construir_sidebar(self) -> None:
        frame_logo: tk.Frame = tk.Frame(self.sidebar, bg=COLORS["bg_sidebar"], pady=20)
        frame_logo.pack(fill="x")
        
        tk.Label(frame_logo, text="📦 Nexus WMS", font=("Segoe UI", 16, "bold"), 
                 bg=COLORS["bg_sidebar"], fg=COLORS["text_dark"]).pack()

        # Lista de tuplas: (Icono, Texto, Es_Activo)
        items: List[Tuple[str, str, bool]] = [
            ("📊", "Dashboard", False),
            ("📦", "Inventory", True),
            ("📄", "Orders", False),
            ("🚚", "Shipments", False),
            ("📈", "Reports", False)
        ]

        for icon, text, is_active in items:
            bg_color: str = COLORS["primary_light"] if is_active else COLORS["bg_sidebar"]
            fg_color: str = COLORS["primary"] if is_active else COLORS["text_gray"]
            font_style: Union[Tuple[str, int, str], Tuple[str, int]] = \
                ("Segoe UI", 10, "bold") if is_active else ("Segoe UI", 10)
            
            item_frame: tk.Frame = tk.Frame(self.sidebar, bg=bg_color, height=45)
            item_frame.pack(fill="x", padx=10, pady=2)
            item_frame.pack_propagate(False)
            
            lbl_icon: tk.Label = tk.Label(item_frame, text=icon, bg=bg_color, fg=fg_color, font=("Arial", 12))
            lbl_icon.pack(side="left", padx=(15, 10))
            
            lbl_text: tk.Label = tk.Label(item_frame, text=text, bg=bg_color, fg=fg_color, font=font_style)
            lbl_text.pack(side="left")

            if is_active:
                tk.Frame(item_frame, bg=COLORS["primary"], width=4).pack(side="left", fill="y", before=lbl_icon)

        user_frame: tk.Frame = tk.Frame(self.sidebar, bg=COLORS["bg_sidebar"], pady=20)
        user_frame.pack(side="bottom", fill="x")
        tk.Label(user_frame, text="👤", font=("Arial", 18), bg=COLORS["bg_sidebar"]).pack(side="left", padx=15)
        
        info_frame: tk.Frame = tk.Frame(user_frame, bg=COLORS["bg_sidebar"])
        info_frame.pack(side="left")
        tk.Label(info_frame, text="Admin User", font=("Segoe UI", 10, "bold"), bg=COLORS["bg_sidebar"]).pack(anchor="w")
        tk.Label(info_frame, text="Logistics Manager", font=("Segoe UI", 8), fg=COLORS["text_gray"], bg=COLORS["bg_sidebar"]).pack(anchor="w")

    def _construir_topbar(self) -> None:
        top_frame: tk.Frame = tk.Frame(self.main_area, bg=COLORS["bg_main"], pady=20, padx=30)
        top_frame.pack(fill="x")

        search_container: tk.Frame = tk.Frame(top_frame, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        search_container.pack(side="left", ipady=5, ipadx=5)
        
        tk.Label(search_container, text="🔍", bg="white", fg=COLORS["text_gray"]).pack(side="left", padx=5)
        
        #luis: converti el texto en un placeholder se puede usar en varias partes ya que es una clase
        #entry_search = tk.Entry(search_container, bg="white", bd=0, font=FONT_BODY, width=30)
        #entry_search.pack(side="left")
        #entry_search.insert(0, "Buscar por SKU, Nombre...")
        entry_search: EntryWithPlaceholder = EntryWithPlaceholder(
            search_container, 
            placeholder="Buscar por SKU, Nombre...",
            bg="white", 
            bd=0, 
            font=FONT_BODY, 
            width=30,
            fg=COLORS["text_gray"]
        )
        entry_search.pack(side="left")

        btn_add: tk.Button = tk.Button(top_frame, text="＋ Add Product", bg=COLORS["primary"], fg="white", 
                            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=5, cursor="hand2",
                            command=self.abrir_modal_nuevo_producto)
        btn_add.pack(side="right")
        
        btn_export: tk.Button = tk.Button(top_frame, text="⬇ Export", bg="white", fg=COLORS["text_dark"], 
                               font=("Segoe UI", 10), relief="solid", bd=0, highlightthickness=1, 
                               highlightbackground=COLORS["border"], padx=15, pady=5, cursor="hand2")
        btn_export.pack(side="right", padx=10)

    def _construir_lista_productos(self) -> None:
        list_container: tk.Frame = tk.Frame(self.main_area, bg="white")
        list_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        header_frame: tk.Frame = tk.Frame(list_container, bg="white", height=50)
        header_frame.pack(fill="x", pady=5)
        
        headers: List[str] = ["PRODUCTO / SKU", "CANTIDAD", "UBICACIÓN", "ESTADO", "ACCIONES"]
        widths: List[int] = [40, 20, 20, 15, 10]

        for i, (text, w) in enumerate(zip(headers, widths)):
            header_frame.columnconfigure(i, weight=w)
            lbl: tk.Label = tk.Label(header_frame, text=text, font=("Segoe UI", 8, "bold"), fg=COLORS["text_gray"], bg="white", anchor="w")
            lbl.grid(row=0, column=i, sticky="we", padx=10, pady=15)

        tk.Frame(list_container, bg=COLORS["border"], height=1).pack(fill="x")

        self.canvas = tk.Canvas(list_container, bg="white", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")) if self.canvas else None
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=950)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.cargar_datos()

    def cargar_datos(self) -> None:
        if not self.scrollable_frame: return

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # productos es una lista de tuplas de la DB
        productos: List[Tuple[int, str, str, str, int, str]] = get_all_products() 
        
        for p in productos:
            p_id, name, sku, cat, stock, loc = p
            
            status_info: Tuple[str, str]
            if stock > 50:
                status_info = ("Available", "success")
            elif stock > 0:
                status_info = ("Low Stock", "info")
            else:
                status_info = ("Out of Stock", "warning")

            self._crear_fila_producto(name, sku, stock, loc, status_info)

    def _crear_fila_producto(self, name: str, sku: str, stock: int, location: str, status_info: Tuple[str, str]) -> None:
        if not self.scrollable_frame: return

        row: tk.Frame = tk.Frame(self.scrollable_frame, bg="white", pady=10)
        row.pack(fill="x", padx=5)

        for i in range(5): row.columnconfigure(i, weight=1)

        # 1. Columna Producto
        frame_prod: tk.Frame = tk.Frame(row, bg="white")
        frame_prod.grid(row=0, column=0, sticky="w", padx=10)
        
        icon_box: tk.Label = tk.Label(frame_prod, text="📷", font=("Arial", 14), bg="#F3F4F6", fg=COLORS["text_gray"], width=4, height=2)
        icon_box.pack(side="left", padx=(0, 10))
        
        text_box: tk.Frame = tk.Frame(frame_prod, bg="white")
        text_box.pack(side="left")
        tk.Label(text_box, text=name, font=("Segoe UI", 10, "bold"), bg="white", fg=COLORS["text_dark"]).pack(anchor="w")
        tk.Label(text_box, text=f"SKU: {sku}", font=("Segoe UI", 8), bg="white", fg=COLORS["text_gray"]).pack(anchor="w")

        # 2. Columna Cantidad
        frame_qty: tk.Frame = tk.Frame(row, bg="white")
        frame_qty.grid(row=0, column=1, sticky="w", padx=10)
        tk.Label(frame_qty, text=f"{stock} Units", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor="w")
        
        boxes: int = stock // 12
        tk.Label(frame_qty, text=f"{boxes} Boxes", font=("Segoe UI", 8), fg=COLORS["text_gray"], bg="white").pack(anchor="w")

        # 3. Columna Ubicación
        loc_frame: tk.Frame = tk.Frame(row, bg="#F3F4F6", padx=8, pady=2)
        loc_frame.grid(row=0, column=2, sticky="w", padx=10)
        tk.Label(loc_frame, text=f"📍 {location}", font=("Segoe UI", 9), bg="#F3F4F6", fg=COLORS["text_dark"]).pack()

        # 4. Columna Estado
        st_text, st_type = status_info
        colors_map: Dict[str, Tuple[str, str]] = {
            "success": (COLORS["success_bg"], COLORS["success_fg"]),
            "warning": (COLORS["warning_bg"], COLORS["warning_fg"]),
            "info": (COLORS["info_bg"], COLORS["info_fg"])
        }
        bg_st, fg_st = colors_map.get(st_type, ("#FFFFFF", "#000000"))
        
        status_frame: tk.Frame = tk.Frame(row, bg=bg_st, padx=10, pady=2)
        status_frame.grid(row=0, column=3, sticky="w", padx=10)
        tk.Label(status_frame, text=f"• {st_text}", font=("Segoe UI", 8, "bold"), bg=bg_st, fg=fg_st).pack()

        # 5. Acciones
        tk.Button(row, text="⋮", font=("Arial", 12, "bold"), bg="white", bd=0, fg=COLORS["text_gray"], cursor="hand2").grid(row=0, column=4)

        tk.Frame(self.scrollable_frame, bg=COLORS["bg_main"], height=1).pack(fill="x", pady=5)

    def abrir_modal_nuevo_producto(self) -> None:
        modal: Toplevel = Toplevel(self)
        modal.title("Nuevo Producto")
        modal.geometry("400x500")
        modal.configure(bg="white")
        modal.grab_set() # Bloquear ventana principal
        
        tk.Label(modal, text="Agregar Producto", font=FONT_H2, bg="white").pack(pady=15)
        
        form: tk.Frame = tk.Frame(modal, bg="white", padx=20)
        form.pack(fill="both", expand=True)

        entries: Dict[str, tk.Entry] = {}
        campos: List[Tuple[str, str]] = [
            ("Nombre", "name"), ("Código Barra", "barcode"), ("Categoría", "category"), 
            ("Pasillo", "aisle"), ("Estante", "shelf"), ("Nivel", "level")
        ]
        
        for label, key in campos:
            tk.Label(form, text=label, bg="white", anchor="w", font=FONT_SMALL).pack(fill="x", pady=(10,0))
            e: tk.Entry = tk.Entry(form, bg="#F9FAFB", relief="flat", highlightbackground="#E5E7EB", highlightthickness=1)
            e.pack(fill="x", ipady=3)
            entries[key] = e

        def guardar() -> None:
            # Tupla de datos tipada para la DB
            data: Tuple[str, str, str, str, str, str, str] = (
                entries["name"].get(),
                entries["barcode"].get(),
                entries["category"].get(),
                "Unidad",
                entries["aisle"].get(),
                entries["shelf"].get(),
                entries["level"].get()
            )
            
            if not data[0] or not data[1]:
                messagebox.showwarning("Atención", "Nombre y Código son obligatorios")
                return
                
            insert_product(data)
            self.cargar_datos()
            modal.destroy()

        btn: tk.Button = tk.Button(modal, text="Guardar Producto", bg=COLORS["primary"], fg="white", 
                        font=("Segoe UI", 10, "bold"), relief="flat", pady=8, command=guardar)
        btn.pack(fill="x", padx=20, pady=20)