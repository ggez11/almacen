import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple, Optional, Union, Any

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
    "badge_in_bg": "#D1FAE5",   "badge_in_fg": "#065F46",
    "badge_out_bg": "#FEF3C7",  "badge_out_fg": "#92400E",
    "blue_dot": "#3B82F6",
    "green_text": "#10B981",
    "red_text": "#EF4444"
}

FontTuple = Union[Tuple[str, int, str], Tuple[str, int]]
FONT_TITLE: FontTuple = ("Segoe UI", 16, "bold")
FONT_HEAD: FontTuple = ("Segoe UI", 8, "bold")
FONT_BODY: FontTuple = ("Segoe UI", 9)
FONT_SMALL: FontTuple = ("Segoe UI", 8)

class MovimientosView(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])

        # Contenedor principal
        self.main_content: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.main_content.pack(fill="both", expand=True, padx=30, pady=20)

        # Referencias para el área de scroll
        self.canvas: Optional[tk.Canvas] = None
        self.scrollable_frame: Optional[tk.Frame] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None

        self._construir_header()
        self._construir_filtros()
        self._construir_tabla_movimientos()

    def _construir_header(self) -> None:
        header_fr: tk.Frame = tk.Frame(self.main_content, bg=COLORS["bg_main"])
        header_fr.pack(fill="x", pady=(0, 15))

        tk.Label(header_fr, text="Inventory  ›  Stock Movements", 
                 fg=COLORS["text_light"], bg=COLORS["bg_main"], font=FONT_SMALL).pack(anchor="w")
        
        title_row: tk.Frame = tk.Frame(header_fr, bg=COLORS["bg_main"])
        title_row.pack(fill="x", pady=(5, 0))
        
        tk.Label(title_row, text="Stock Movements History", 
                 font=FONT_TITLE, bg=COLORS["bg_main"], fg=COLORS["text_header"]).pack(side="left")
        
        # Botón Exportar (Aquí podrías conectar la lógica de CSV más adelante)
        tk.Button(title_row, text="⬇ Export CSV", bg=COLORS["white"], fg=COLORS["text_body"],
                  relief="solid", bd=0, highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=15, pady=6, cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=self._exportar_csv_dummy).pack(side="right")

    def _construir_filtros(self) -> None:
        filter_bar: tk.Frame = tk.Frame(self.main_content, bg=COLORS["white"], padx=15, pady=15,
                                        highlightbackground=COLORS["border"], highlightthickness=1)
        filter_bar.pack(fill="x", pady=(0, 20))

        search_container: tk.Frame = tk.Frame(filter_bar, bg="#F3F4F6", padx=10, pady=5)
        search_container.pack(side="left", fill="y")
        
        tk.Label(search_container, text="🔍", bg="#F3F4F6", fg=COLORS["text_light"]).pack(side="left")
        
        self.search_entry: EntryWithPlaceholder = EntryWithPlaceholder(
            search_container,
            placeholder="Search by Product or Reason...",
            bg="#F3F4F6",
            bd=0,
            width=40,
            font=FONT_BODY,
            fg=COLORS["text_body"]
        )
        self.search_entry.pack(side="left", padx=5)

        tk.Button(filter_bar, text="Clear Filters", fg=COLORS["primary"], bg=COLORS["white"], 
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", 
                  command=self.search_entry.clear).pack(side="left", padx=15)

    def _construir_tabla_movimientos(self) -> None:
        table_container: tk.Frame = tk.Frame(self.main_content, bg=COLORS["white"],
                                             highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True)

        # Header de Columnas
        headers: List[str] = ["DATE & TIME", "PRODUCT", "TYPE", "QTY", "REASON", "USER"]
        widths: List[int] = [18, 35, 12, 10, 15, 10]
        
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

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=1000)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.cargar_datos_historial()

    def cargar_datos_historial(self) -> None:
        """Consulta la DB y refresca la lista de movimientos."""
        if not self.scrollable_frame: return

        # Limpiar tabla
        for w in self.scrollable_frame.winfo_children(): w.destroy()

        # Obtener datos reales de la base de datos
        movimientos: List[Tuple[Any, ...]] = get_movements_history() 

        for mov in movimientos:
            # Desempaquetado basado en tu consulta SQL: (fecha, producto, usuario, tipo, concepto, cantidad)
            fecha, prod, user, tipo, motivo, cantidad = mov
            self._crear_fila(fecha, prod, tipo, cantidad, motivo, user)

    def _crear_fila(self, date_time: str, prod_name: str, move_type: str, 
                    qty: int, reason: str, user: str) -> None:
        if not self.scrollable_frame: return

        row: tk.Frame = tk.Frame(self.scrollable_frame, bg=COLORS["white"], pady=12)
        row.pack(fill="x")
        
        widths: List[int] = [18, 35, 12, 10, 15, 10]
        for i, w in enumerate(widths): row.columnconfigure(i, weight=w)

        # 1. Date & Time
        tk.Label(row, text=date_time, font=FONT_BODY, bg=COLORS["white"], 
                 fg=COLORS["text_body"]).grid(row=0, column=0, sticky="w", padx=15)

        # 2. Product
        tk.Label(row, text=f"📦 {prod_name}", font=("Segoe UI", 9, "bold"), 
                 bg=COLORS["white"], fg=COLORS["text_header"]).grid(row=0, column=1, sticky="w", padx=15)

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
        tk.Label(row, text=f"{prefix}{qty}", font=("Segoe UI", 9, "bold"), 
                 bg=COLORS["white"], fg=color_q).grid(row=0, column=3, sticky="w", padx=15)

        # 5. Reason
        tk.Label(row, text=reason, font=FONT_BODY, bg=COLORS["white"], 
                 fg=COLORS["text_body"]).grid(row=0, column=4, sticky="w", padx=15)

        # 6. User
        tk.Label(row, text=f"👤 {user}", font=FONT_SMALL, bg=COLORS["white"], 
                 fg=COLORS["text_light"]).grid(row=0, column=5, sticky="w", padx=15)

        # Línea divisoria
        tk.Frame(self.scrollable_frame, bg=COLORS["border"], height=1).pack(fill="x")

    def _exportar_csv_dummy(self) -> None:
        messagebox.showinfo("Export", "Exporting history to CSV...")