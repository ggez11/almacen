import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple, Union, Optional

# Importaciones del sistema
from database.queries import get_all_products
from gui.components.widgets import EntryWithPlaceholder

# --- CONFIGURACIÓN DE ESTILOS (Tema Azul - Ventas) ---
COLORS: Dict[str, str] = {
    "bg_main": "#F8F9FA",
    "bg_panel": "#FFFFFF",
    "primary": "#2563EB",       # Azul fuerte
    "primary_dark": "#1E40AF",
    "text_dark": "#111827",
    "text_gray": "#6B7280",
    "border": "#E5E7EB",
    "success": "#10B981",
    "danger": "#EF4444"
}

FontTuple = Tuple[str, int, str]

class EnviosView(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])

        # Estado del carrito: Lista de diccionarios
        self.cart_items: List[Dict[str, Union[str, int, float]]] = []

        # Estructura Principal: Panel Izquierdo (Productos) | Panel Derecho (Carrito)
        self.left_panel: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)

        self.right_panel: tk.Frame = tk.Frame(self, bg=COLORS["bg_panel"], width=400, 
                                              highlightbackground=COLORS["border"], highlightthickness=1)
        self.right_panel.pack(side="right", fill="y", padx=(0, 0))
        self.right_panel.pack_propagate(False)

        # Construcción de UI
        self._construir_panel_izquierdo()
        self._construir_panel_derecho()
        
        # Cargar datos iniciales
        self.cargar_productos()

    def _construir_panel_izquierdo(self) -> None:
        # --- Top Bar (Búsqueda) ---
        top_bar: tk.Frame = tk.Frame(self.left_panel, bg=COLORS["bg_main"])
        top_bar.pack(fill="x", pady=(0, 15))

        search_cont: tk.Frame = tk.Frame(top_bar, bg="white", highlightbackground=COLORS["primary"], highlightthickness=1)
        search_cont.pack(side="left", fill="x", expand=True, ipady=5)

        tk.Label(search_cont, text=" 🔍 ", bg="white").pack(side="left")
        
        self.entry_search: EntryWithPlaceholder = EntryWithPlaceholder(
            search_cont, placeholder="Escanear SKU o buscar producto...", 
            bg="white", bd=0, width=40
        )
        self.entry_search.pack(side="left", fill="x", expand=True)

        # --- Cabecera de la Tabla ---
        headers: List[str] = ["SKU", "DESCRIPCIÓN", "UBICACIÓN", "STOCK", "ACCIÓN"]
        widths: List[int] = [15, 40, 15, 10, 10]
        
        head_fr: tk.Frame = tk.Frame(self.left_panel, bg=COLORS["bg_main"])
        head_fr.pack(fill="x", pady=5)
        
        for i, text in enumerate(headers):
            head_fr.columnconfigure(i, weight=widths[i])
            tk.Label(head_fr, text=text, font=("Segoe UI", 8, "bold"), 
                     bg=COLORS["bg_main"], fg=COLORS["text_gray"], anchor="w").grid(row=0, column=i, sticky="we")

        # --- Área de Scroll para Productos ---
        self.canvas_prod = tk.Canvas(self.left_panel, bg=COLORS["bg_main"], highlightthickness=0)
        self.scroll_prod = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.canvas_prod.yview)
        self.frame_list = tk.Frame(self.canvas_prod, bg=COLORS["bg_main"])

        self.frame_list.bind(
            "<Configure>", 
            lambda e: self.canvas_prod.configure(scrollregion=self.canvas_prod.bbox("all"))
        )
        
        self.canvas_prod.create_window((0, 0), window=self.frame_list, anchor="nw", width=800) # Width estimado
        self.canvas_prod.configure(yscrollcommand=self.scroll_prod.set)
        
        self.canvas_prod.pack(side="left", fill="both", expand=True)
        self.scroll_prod.pack(side="right", fill="y")

    def _construir_panel_derecho(self) -> None:
        # --- Header Total ---
        header: tk.Frame = tk.Frame(self.right_panel, bg=COLORS["primary"], padx=20, pady=20)
        header.pack(fill="x")
        
        tk.Label(header, text="Total Venta", fg="#BFDBFE", bg=COLORS["primary"], font=("Segoe UI", 10)).pack(anchor="w")
        self.lbl_total: tk.Label = tk.Label(header, text="$ 0.00", fg="white", bg=COLORS["primary"], 
                                            font=("Segoe UI", 24, "bold"))
        self.lbl_total.pack(anchor="w")

        # --- Configuración de Salida ---
        config_fr: tk.Frame = tk.Frame(self.right_panel, bg="white", padx=20, pady=15)
        config_fr.pack(fill="x")
        
        tk.Label(config_fr, text="Tipo de Operación:", font=("Segoe UI", 9), bg="white", fg=COLORS["text_gray"]).pack(anchor="w")
        self.combo_ops: ttk.Combobox = ttk.Combobox(config_fr, values=["Venta Directa", "Pedido Web", "Transferencia"], state="readonly")
        self.combo_ops.current(0)
        self.combo_ops.pack(fill="x", pady=(5, 0))

        tk.Label(config_fr, text="Carrito (Items):", font=("Segoe UI", 9, "bold"), bg="white", fg=COLORS["text_dark"]).pack(anchor="w", pady=(20, 5))

        # --- Lista del Carrito ---
        self.cart_container: tk.Frame = tk.Frame(self.right_panel, bg="white")
        self.cart_container.pack(fill="both", expand=True, padx=10)

        # --- Botón Acción ---
        btn_fr: tk.Frame = tk.Frame(self.right_panel, bg="white", padx=20, pady=20)
        btn_fr.pack(side="bottom", fill="x")
        
        tk.Button(btn_fr, text="Procesar Salida →", bg=COLORS["primary"], fg="white", 
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=10, cursor="hand2",
                  command=self.procesar_venta).pack(fill="x")

    def cargar_productos(self) -> None:
        # Limpiar lista visual
        for widget in self.frame_list.winfo_children():
            widget.destroy()

        # Obtener productos de la DB (usamos get_all_products importado)
        # Asumimos que get_all_products devuelve [(id, name, sku, cat, stock, loc), ...]
        try:
            productos = get_all_products()
        except Exception:
            productos = [] # Fallback si falla la DB

        for p in productos:
            # Desempaquetado seguro (ajusta índices según tu query real)
            # p: (id, name, sku, category, stock, location)
            self._crear_fila_producto(p[1], p[2], p[5], p[4], 10.00) # Precio dummy 10.00

    def _crear_fila_producto(self, name: str, sku: str, loc: str, stock: int, price: float) -> None:
        row: tk.Frame = tk.Frame(self.frame_list, bg="white", pady=10, padx=5)
        row.pack(fill="x", pady=2)

        # Grid config
        for i, w in enumerate([15, 40, 15, 10, 10]): row.columnconfigure(i, weight=w)

        tk.Label(row, text=sku, font=("Segoe UI", 9), bg="white", fg=COLORS["text_gray"]).grid(row=0, column=0)
        
        # Descripción
        tk.Label(row, text=name, font=("Segoe UI", 9, "bold"), bg="white", anchor="w").grid(row=0, column=1, sticky="w")
        
        # Ubicación
        tk.Label(row, text=loc, font=("Consolas", 9), bg="#F3F4F6", padx=5).grid(row=0, column=2)
        
        # Stock con color
        color_st: str = COLORS["success"] if stock > 10 else COLORS["danger"]
        tk.Label(row, text=str(stock), font=("Segoe UI", 9, "bold"), bg="white", fg=color_st).grid(row=0, column=3)

        # Botón Agregar
        btn: tk.Button = tk.Button(row, text="＋", bg=COLORS["primary"], fg="white", bd=0, width=3, cursor="hand2",
                                   command=lambda: self.agregar_al_carrito(name, sku, price))
        btn.grid(row=0, column=4)

    def agregar_al_carrito(self, name: str, sku: str, price: float) -> None:
        # Lógica simple de carrito visual
        self.cart_items.append({"name": name, "sku": sku, "price": price, "qty": 1})
        self._renderizar_carrito()

    def _renderizar_carrito(self) -> None:
        for w in self.cart_container.winfo_children(): w.destroy()
        
        total: float = 0.0
        
        for item in self.cart_items:
            subtotal = float(item["price"]) * int(item["qty"]) # type: ignore
            total += subtotal
            
            row = tk.Frame(self.cart_container, bg="white", pady=5, highlightbackground=COLORS["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            
            tk.Label(row, text=f"{item['name']}", font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w", padx=5)
            
            info = tk.Frame(row, bg="white")
            info.pack(fill="x", padx=5)
            tk.Label(info, text=f"{item['sku']}", font=("Segoe UI", 8), fg=COLORS["text_gray"], bg="white").pack(side="left")
            tk.Label(info, text=f"${subtotal:.2f}", font=("Segoe UI", 9), bg="white").pack(side="right")

        self.lbl_total.config(text=f"$ {total:,.2f}")

    def procesar_venta(self) -> None:
        if not self.cart_items:
            messagebox.showwarning("Vacío", "El carrito está vacío.")
            return
        
        # Aquí iría la llamada al service para procesar la transacción
        messagebox.showinfo("Procesado", "Venta registrada exitosamente (Simulación)")
        self.cart_items.clear()
        self._renderizar_carrito()