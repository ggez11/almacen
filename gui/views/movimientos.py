import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Optional, Union

# Importaciones locales
from database.queries import get_movements_history
from gui.components.widgets import EntryWithPlaceholder

# --- CONFIGURACIÓN DE COLORES Y ESTILOS ---
COLORS: Dict[str, str] = {
    "bg_main": "#F8F9FA",
    "bg_sidebar": "#FFFFFF",
    "white": "#FFFFFF",
    "text_header": "#111827",
    "text_body": "#374151",
    "text_light": "#9CA3AF",
    "border": "#E5E7EB",
    "primary": "#0D9488",
    "primary_light": "#E0F2F1",
    # Badges
    "badge_in_bg": "#D1FAE5",   "badge_in_fg": "#065F46",
    "badge_out_bg": "#FEF3C7",  "badge_out_fg": "#92400E",
    "blue_dot": "#3B82F6",
    "green_text": "#10B981",
    "red_text": "#EF4444"
}

# Tipado para fuentes
FontTuple = Union[Tuple[str, int, str], Tuple[str, int]]
FONT_TITLE: FontTuple = ("Segoe UI", 16, "bold")
FONT_HEAD: FontTuple = ("Segoe UI", 8, "bold")
FONT_BODY: FontTuple = ("Segoe UI", 9)
FONT_SMALL: FontTuple = ("Segoe UI", 8)

class MovimientosView(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])

        # Atributos de instancia tipados
        self.container: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.container.pack(fill="both", expand=True)

        # Referencias para el área de scroll
        self.canvas: Optional[tk.Canvas] = None
        self.scrollable_frame: Optional[tk.Frame] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None

        # Construir la interfaz
        self._construir_sidebar()
        
        self.main_content: tk.Frame = tk.Frame(self.container, bg=COLORS["bg_main"])
        self.main_content.pack(side="right", fill="both", expand=True, padx=30, pady=20)

        self._construir_header()
        self._construir_filtros()
        self._construir_tabla_movimientos()

    def _construir_sidebar(self) -> None:
        sidebar: tk.Frame = tk.Frame(self.container, bg=COLORS["bg_sidebar"], width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo
        logo_frame: tk.Frame = tk.Frame(sidebar, bg=COLORS["bg_sidebar"], pady=30)
        logo_frame.pack(fill="x")
        tk.Label(logo_frame, text="📦 Nexus WMS", font=("Segoe UI", 14, "bold"), 
                 bg=COLORS["bg_sidebar"], fg=COLORS["text_header"]).pack()

        # Menu Items tipados
        items: List[Tuple[str, str, bool]] = [
            ("📊", "Dashboard", False),
            ("📦", "Inventory", True),
            ("📄", "Orders", False),
            ("🚚", "Shipments", False),
            ("📈", "Reports", False),
            ("⚙️", "Settings", False)
        ]

        for icon, text, is_active in items:
            bg: str = COLORS["primary_light"] if is_active else COLORS["bg_sidebar"]
            fg: str = COLORS["primary"] if is_active else COLORS["text_body"]
            
            item_fr: tk.Frame = tk.Frame(sidebar, bg=bg, height=40)
            item_fr.pack(fill="x", padx=10, pady=2)
            item_fr.pack_propagate(False)
            
            if is_active:
                tk.Frame(item_fr, bg=COLORS["primary"], width=4).pack(side="left", fill="y")
            
            tk.Label(item_fr, text=f"{icon}  {text}", bg=bg, fg=fg, 
                     font=("Segoe UI", 10, "bold" if is_active else "normal")).pack(side="left", padx=15)

    def _construir_header(self) -> None:
        header_fr: tk.Frame = tk.Frame(self.main_content, bg=COLORS["bg_main"])
        header_fr.pack(fill="x", pady=(0, 15))

        tk.Label(header_fr, text="Inventory  ›  Stock Movements", 
                 fg=COLORS["text_light"], bg=COLORS["bg_main"], font=FONT_SMALL).pack(anchor="w")
        
        title_row: tk.Frame = tk.Frame(header_fr, bg=COLORS["bg_main"])
        title_row.pack(fill="x", pady=(5, 0))
        
        tk.Label(title_row, text="Stock Movements History", 
                 font=FONT_TITLE, bg=COLORS["bg_main"], fg=COLORS["text_header"]).pack(side="left")
        
        # Botón Exportar estilizado
        tk.Button(title_row, text="⬇ Export CSV", bg=COLORS["white"], fg=COLORS["text_body"],
                  relief="solid", bd=0, highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=15, pady=6, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="right")

    def _construir_filtros(self) -> None:
        filter_bar: tk.Frame = tk.Frame(self.main_content, bg=COLORS["white"], padx=15, pady=15,
                                       highlightbackground=COLORS["border"], highlightthickness=1)
        filter_bar.pack(fill="x", pady=(0, 20))

        # Buscador usando el nuevo Widget personalizado
        search_container: tk.Frame = tk.Frame(filter_bar, bg="#F3F4F6", padx=10, pady=5)
        search_container.pack(side="left", fill="y")
        
        tk.Label(search_container, text="🔍", bg="#F3F4F6", fg=COLORS["text_light"]).pack(side="left")
        
        self.search_entry: EntryWithPlaceholder = EntryWithPlaceholder(
            search_container,
            placeholder="Search by Product name, SKU or Location...",
            bg="#F3F4F6",
            bd=0,
            width=40,
            font=FONT_BODY,
            fg=COLORS["text_body"]
        )
        self.search_entry.pack(side="left", padx=5)

        # Filtros adicionales
        self._crear_filtro_fake(filter_bar, "📅 Last 30 Days")
        self._crear_filtro_fake(filter_bar, "🌪 All Reasons")

        tk.Button(filter_bar, text="Clear Filters", fg=COLORS["primary"], bg=COLORS["white"], 
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", 
                  command=self.search_entry.clear).pack(side="left", padx=15)

    def _crear_filtro_fake(self, parent: tk.Widget, text: str) -> None:
        f: tk.Frame = tk.Frame(parent, bg=COLORS["white"], highlightbackground=COLORS["border"], 
                               highlightthickness=1, padx=10, pady=5)
        f.pack(side="left", padx=(10, 0))
        tk.Label(f, text=text, bg=COLORS["white"], fg=COLORS["text_body"], font=FONT_BODY).pack(side="left")
        tk.Label(f, text=" ▼", bg=COLORS["white"], fg=COLORS["text_light"], font=FONT_SMALL).pack(side="left")

    def _construir_tabla_movimientos(self) -> None:
        table_container: tk.Frame = tk.Frame(self.main_content, bg=COLORS["white"],
                                             highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True)

        # Header de Columnas
        headers: List[str] = ["DATE & TIME", "PRODUCT / SKU", "TYPE", "QTY", "REASON", "LOCATION", "USER"]
        widths: List[int] = [15, 30, 10, 8, 15, 10, 12]
        
        header_fr: tk.Frame = tk.Frame(table_container, bg="#F9FAFB", height=45)
        header_fr.pack(fill="x")
        header_fr.pack_propagate(False)

        for i, (h_text, w) in enumerate(zip(headers, widths)):
            header_fr.columnconfigure(i, weight=w)
            tk.Label(header_fr, text=h_text, bg="#F9FAFB", fg=COLORS["text_light"], 
                     font=FONT_HEAD, anchor="w").grid(row=0, column=i, sticky="we", padx=15, pady=12)

        # Área scrolleable
        self.canvas = tk.Canvas(table_container, bg=COLORS["white"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS["white"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")) if self.canvas else None
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=1050)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.cargar_datos_historial()

    def cargar_datos_historial(self) -> None:
        if not self.scrollable_frame: return

        for w in self.scrollable_frame.winfo_children(): w.destroy()

        # Datos desde DB (Tupla tipada)
        movimientos: List[Tuple[str, str, str, str, str, int]] = get_movements_history() 

        for mov in movimientos:
            # (timestamp, prod_name, user, tipo, concepto, qty)
            fecha, prod, user, tipo, motivo, cantidad = mov
            
            # Datos visuales extendidos (Simulados para el diseño)
            sku: str = f"SKU-{str(abs(hash(prod)))[:5]}"
            loc: str = "A-12-04" 

            self._crear_fila(fecha, prod, sku, tipo, cantidad, motivo, loc, user)

    def _crear_fila(self, date_time: str, prod_name: str, sku: str, move_type: str, 
                    qty: int, reason: str, location: str, user: str) -> None:
        if not self.scrollable_frame: return

        row: tk.Frame = tk.Frame(self.scrollable_frame, bg=COLORS["white"], pady=12)
        row.pack(fill="x")
        
        widths: List[int] = [15, 30, 10, 8, 15, 10, 12]
        for i, w in enumerate(widths): row.columnconfigure(i, weight=w)

        # 1. Date & Time
        date_fr: tk.Frame = tk.Frame(row, bg=COLORS["white"])
        date_fr.grid(row=0, column=0, sticky="w", padx=15)
        
        parts: List[str] = date_time.split(" ")
        d_txt: str = parts[0]
        t_txt: str = parts[1][:5] if len(parts) > 1 else ""
        
        tk.Label(date_fr, text=d_txt, font=("Segoe UI", 9, "bold"), bg=COLORS["white"], fg=COLORS["text_body"]).pack(anchor="w")
        tk.Label(date_fr, text=t_txt, font=FONT_SMALL, bg=COLORS["white"], fg=COLORS["text_light"]).pack(anchor="w")

        # 2. Product
        prod_fr: tk.Frame = tk.Frame(row, bg=COLORS["white"])
        prod_fr.grid(row=0, column=1, sticky="w", padx=15)
        tk.Label(prod_fr, text="📦", font=("Arial", 14), bg="#F3F4F6", width=3).pack(side="left", padx=(0,10))
        
        txt_fr: tk.Frame = tk.Frame(prod_fr, bg=COLORS["white"])
        txt_fr.pack(side="left")
        tk.Label(txt_fr, text=prod_name, font=("Segoe UI", 9, "bold"), bg=COLORS["white"], fg=COLORS["text_header"]).pack(anchor="w")
        tk.Label(txt_fr, text=sku, font=FONT_SMALL, bg=COLORS["white"], fg=COLORS["text_light"]).pack(anchor="w")

        # 3. Type Badge
        es_entrada: bool = move_type.upper() == "ENTRADA"
        bg_b: str = COLORS["badge_in_bg"] if es_entrada else COLORS["badge_out_bg"]
        fg_b: str = COLORS["badge_in_fg"] if es_entrada else COLORS["badge_out_fg"]
        
        badge: tk.Frame = tk.Frame(row, bg=bg_b, padx=8, pady=3)
        badge.grid(row=0, column=2, sticky="w", padx=15)
        tk.Label(badge, text="↓ IN" if es_entrada else "↑ OUT", font=FONT_HEAD, bg=bg_b, fg=fg_b).pack()

        # 4. Qty
        color_q: str = COLORS["green_text"] if es_entrada else COLORS["red_text"]
        prefix: str = "+" if es_entrada else "-"
        tk.Label(row, text=f"{prefix}{qty}", font=("Segoe UI", 9, "bold"), bg=COLORS["white"], fg=color_q)\
            .grid(row=0, column=3, sticky="w", padx=15)

        # 5. Reason
        re_fr: tk.Frame = tk.Frame(row, bg=COLORS["white"])
        re_fr.grid(row=0, column=4, sticky="w", padx=15)
        tk.Label(re_fr, text="●", fg=COLORS["blue_dot"], bg=COLORS["white"], font=("Arial", 8)).pack(side="left", padx=(0,5))
        tk.Label(re_fr, text=reason, font=FONT_BODY, bg=COLORS["white"], fg=COLORS["text_body"]).pack(side="left")

        # 6. Location
        loc_fr: tk.Frame = tk.Frame(row, bg="#F3F4F6", padx=8, pady=2)
        loc_fr.grid(row=0, column=5, sticky="w", padx=15)
        tk.Label(loc_fr, text=location, font=("Consolas", 8), bg="#F3F4F6", fg=COLORS["text_body"]).pack()

        # 7. User
        u_fr: tk.Frame = tk.Frame(row, bg=COLORS["white"])
        u_fr.grid(row=0, column=6, sticky="w", padx=15)
        tk.Label(u_fr, text="👤", font=("Arial", 12), bg=COLORS["white"]).pack(side="left", padx=(0,5))
        tk.Label(u_fr, text=user, font=FONT_BODY, bg=COLORS["white"], fg=COLORS["text_body"]).pack(side="left")

        tk.Frame(self.scrollable_frame, bg=COLORS["border"], height=1).pack(fill="x")