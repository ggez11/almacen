import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from typing import Dict, List, Tuple, Any, Optional

# Importaciones locales
# Se agregaron delete_product y update_product
from database.queries import get_all_products, insert_product, delete_product, update_product
from gui.components.widgets import EntryWithPlaceholder
from gui.components.tooltip import ToolTip
from services.inv_manager import InventoryManager, State

# --- CONFIGURACIÓN DE ESTILOS ---
COLORS: Dict[str, str] = {
    "bg_main": "#F3F4F6",
    "primary": "#0D9488",
    "text_dark": "#111827",
    "text_gray": "#6B7280",
    "border": "#E5E7EB",
    "white": "#FFFFFF",
    "out_of_stock_bg": "#E5E7EB", 
    "success_bg": "#D1FAE5", "success_fg": "#065F46",
    "warning_bg": "#FEF3C7", "warning_fg": "#92400E",
    "info_bg": "#DBEAFE",    "info_fg": "#1E40AF"
}

COLUMN_WEIGHTS: List[int] = [7, 5, 5, 5, 5]

FONT_H2: Tuple[str, int, str] = ("Segoe UI", 12, "bold")
FONT_BODY: Tuple[str, int] = ("Segoe UI", 10)
FONT_BODY_BOLD: Tuple[str, int, str] = ("Segoe UI", 10, "bold")
FONT_SMALL: Tuple[str, int] = ("Segoe UI", 9)

class InventarioView(tk.Frame):
    def __init__(self, parent: tk.Widget, controller: Any = None) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])
        
        self.inv_manager: InventoryManager = getattr(controller, 'inv_manager', InventoryManager())
        self.current_user_id: int = getattr(controller, 'current_user_id', 1)

        self.main_area: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.main_area.pack(fill="both", expand=True)

        self._construir_topbar()
        self._construir_lista_productos()

    def _construir_topbar(self) -> None:
        top_frame: tk.Frame = tk.Frame(self.main_area, bg=COLORS["bg_main"], pady=20, padx=30)
        top_frame.pack(fill="x")

        search_container: tk.Frame = tk.Frame(top_frame, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        search_container.pack(side="left", ipady=5, ipadx=5)
        
        tk.Label(search_container, text="🔍", bg="white", fg=COLORS["text_gray"]).pack(side="left", padx=5)
        
        self.entry_search: EntryWithPlaceholder = EntryWithPlaceholder(
            search_container, 
            placeholder="Buscar por SKU, Nombre...",
            bg="white", bd=0, font=FONT_BODY, width=30, fg=COLORS["text_gray"]
        )
        self.entry_search.pack(side="left")

        tk.Button(top_frame, text="＋ Add Product", bg=COLORS["primary"], fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=5, 
                  cursor="hand2", command=self.abrir_modal_nuevo_producto).pack(side="right")

    def _construir_lista_productos(self) -> None:
        list_container: tk.Frame = tk.Frame(self.main_area, bg="white")
        list_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        header_frame: tk.Frame = tk.Frame(list_container, bg="white")
        header_frame.pack(fill="x", padx=5)
        
        headers: List[str] = ["PRODUCTO / SKU", "CANTIDAD", "UBICACIÓN", "ESTADO", "ACCIONES"]
        for i, (text, weight) in enumerate(zip(headers, COLUMN_WEIGHTS)):
            header_frame.columnconfigure(i, weight=weight, uniform="table_col")
            tk.Label(header_frame, text=text, font=("Segoe UI", 8, "bold"),
                    fg=COLORS["text_gray"], bg="white", anchor="w").grid(row=0, column=i, sticky="we", padx=10, pady=15)

        self.canvas = tk.Canvas(list_container, bg="white", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.cargar_datos()

    def cargar_datos(self) -> None:
        if not self.scrollable_frame: return
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()

        productos: List[Tuple[int, str, str, str, int, str]] = get_all_products() 
        for p in productos:
            p_id, name, sku, cat, stock, loc = p
            if stock > 50: status_info = ("Available", "success")
            elif stock > 0: status_info = ("Low Stock", "info")
            else: status_info = ("Out of Stock", "warning")
            self._crear_fila_producto(p_id, name, sku, cat, stock, loc, status_info)

    def _crear_fila_producto(self, p_id: int, name: str, sku: str, cat: str, stock: int, 
                             location: str, status_info: Tuple[str, str]) -> None:
    
        is_empty: bool = stock <= 0
        row_bg: str = COLORS["out_of_stock_bg"] if is_empty else COLORS["white"]
        text_color: str = COLORS["text_gray"] if is_empty else COLORS["text_dark"]
        
        row: tk.Frame = tk.Frame(self.scrollable_frame, bg=row_bg, pady=10)
        row.pack(fill="x")
        
        for i, weight in enumerate(COLUMN_WEIGHTS):
            row.columnconfigure(i, weight=weight, uniform="table_col")

        # 1. Producto
        f_prod: tk.Frame = tk.Frame(row, bg=row_bg)
        f_prod.grid(row=0, column=0, sticky="nsew")
        f_prod.columnconfigure(1, weight=1)
        
        tk.Label(f_prod, text="📦", font=("Arial", 12), bg="#EEE", width=3).grid(row=0, column=0, padx=10)
        lbl_name: tk.Label = tk.Label(f_prod, text=name, font=FONT_BODY_BOLD, bg=row_bg, fg=text_color, anchor="w", width=25)
        lbl_name.grid(row=0, column=1, sticky="we")
        
        if len(name) > 25: ToolTip(lbl_name, name)
        tk.Label(f_prod, text=sku, font=FONT_SMALL, fg=COLORS["text_gray"], bg=row_bg, anchor="w").grid(row=1, column=1, sticky="w")

        # 2. Cantidad
        tk.Label(row, text=f"   {stock} Units", font=FONT_BODY_BOLD, bg=row_bg, fg=text_color, anchor="w").grid(row=0, column=1, sticky="we", padx=10)

        # 3. Ubicación
        tk.Label(row, text=f"    📍 {location}", font=FONT_SMALL, bg=row_bg, fg=COLORS["text_gray"], anchor="w").grid(row=0, column=2, sticky="we", padx=10)

        # 4. Estado
        st_text, st_type = status_info
        colors_map = {"success": (COLORS["success_bg"], COLORS["success_fg"]), 
                      "warning": (COLORS["warning_bg"], COLORS["warning_fg"]),
                      "info": (COLORS["info_bg"], COLORS["info_fg"])}      
        bg_st, fg_st = colors_map.get(st_type, ("#DDD", "#333"))
        if is_empty: bg_st, fg_st = "#9CA3AF", "white"

        tk.Label(row, text=st_text.upper(), font=("Segoe UI", 7, "bold"), bg=bg_st, fg=fg_st, padx=5, pady=2).grid(row=0, column=3, sticky="w", padx=10)

        # 5. Acciones (BOTONES REDISEÑADOS)
        f_actions = tk.Frame(row, bg=row_bg)
        f_actions.grid(row=0, column=4, sticky="we", padx=10)

        # Botón Ajustar
        tk.Button(f_actions, text="📊", font=("Segoe UI", 9), fg=COLORS["primary"], bg=row_bg, 
                  relief="flat", cursor="hand2", command=lambda: self._abrir_modal_ajuste(p_id, name)).pack(side="left", padx=2)

        # Botón Editar
        tk.Button(f_actions, text="✏️", font=("Segoe UI", 9), fg="#2563EB", bg=row_bg, 
                  relief="flat", cursor="hand2", command=lambda: self.abrir_modal_editar_producto(p_id, name, sku, cat, location)).pack(side="left", padx=2)

        # Botón Eliminar
        tk.Button(f_actions, text="🗑️", font=("Segoe UI", 9), fg="#DC2626", bg=row_bg, 
                  relief="flat", cursor="hand2", command=lambda: self.confirmar_eliminacion(p_id, name)).pack(side="left", padx=2)

        tk.Frame(self.scrollable_frame, bg=COLORS["border"], height=1).pack(fill="x", padx=10)

    # --- NUEVOS MÉTODOS PARA EDITAR Y ELIMINAR ---

    def confirmar_eliminacion(self, p_id: int, name: str) -> None:
        if messagebox.askyesno("Confirmar", f"¿Eliminar definitivamente '{name}'?"):
            try:
                if delete_product(p_id):
                    messagebox.showinfo("Éxito", "Producto eliminado")
                    self.cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def abrir_modal_editar_producto(self, p_id: int, name: str, sku: str, cat: str, loc: str) -> None:
        modal = Toplevel(self)
        modal.title("Editar Producto")
        modal.geometry("400x550")
        modal.configure(bg="white")
        modal.grab_set()

        tk.Label(modal, text="Editar Producto", font=FONT_H2, bg="white").pack(pady=15)
        form = tk.Frame(modal, bg="white", padx=20)
        form.pack(fill="both", expand=True)

        entries = {}
        campos = [("Nombre", "name", name), ("SKU", "barcode", sku), ("Categoría", "category", cat), ("Ubicación", "location", loc)]

        for label, key, value in campos:
            tk.Label(form, text=label, bg="white", font=FONT_SMALL, fg=COLORS["text_gray"]).pack(fill="x", pady=(10,0))
            e = tk.Entry(form, bg="#F9FAFB", relief="flat", highlightthickness=1, font=FONT_BODY)
            e.insert(0, value)
            e.pack(fill="x", ipady=5)
            entries[key] = e

        def actualizar():
            data = (entries["name"].get(), entries["barcode"].get(), entries["category"].get(), entries["location"].get(), p_id)
            if update_product(data):
                messagebox.showinfo("Éxito", "Producto actualizado")
                self.cargar_datos()
                modal.destroy()

        tk.Button(modal, text="Guardar Cambios", bg=COLORS["primary"], fg="white", font=("Segoe UI", 10, "bold"), 
                  relief="flat", pady=10, command=actualizar).pack(fill="x", padx=20, pady=25)

    # --- MÉTODOS ORIGINALES ---

    def _abrir_modal_ajuste(self, p_id: int, p_name: str) -> None:
        modal = Toplevel(self)
        modal.title("Stock Adjustment")
        modal.geometry("350x450")
        modal.configure(bg="white", padx=20, pady=20)
        modal.grab_set()

        tk.Label(modal, text=f"Ajustar: {p_name}", font=FONT_H2, bg="white", wraplength=300).pack(pady=(0, 20))

        tk.Label(modal, text="Tipo de Movimiento:", bg="white", font=FONT_SMALL).pack(anchor="w")
        combo_tipo = ttk.Combobox(modal, values=["ENTRADA", "SALIDA"], state="readonly")
        combo_tipo.pack(fill="x", pady=5)
        combo_tipo.set("ENTRADA")

        tk.Label(modal, text="Cantidad:", bg="white", font=FONT_SMALL).pack(anchor="w", pady=(10, 0))
        entry_qty = tk.Entry(modal, font=FONT_BODY)
        entry_qty.pack(fill="x", pady=5)

        tk.Label(modal, text="Estado del Stock:", bg="white", font=FONT_SMALL).pack(anchor="w", pady=(10, 0))
        combo_state = ttk.Combobox(modal, values=["Disponible", "Cuarentena", "Dañado"], state="readonly")
        combo_state.pack(fill="x", pady=5)
        combo_state.set("Disponible")

        tk.Label(modal, text="Concepto/Nota:", bg="white", font=FONT_SMALL).pack(anchor="w", pady=(10, 0))
        entry_concept = tk.Entry(modal, font=FONT_BODY)
        entry_concept.pack(fill="x", pady=5)

        def ejecutar_ajuste() -> None:
            try:
                tipo = combo_tipo.get()
                qty = int(entry_qty.get())
                state: State = combo_state.get() # type: ignore
                concept = entry_concept.get() or "Ajuste manual"

                if tipo == "ENTRADA":
                    self.inv_manager.registrar_entrada(p_id, self.current_user_id, qty, state, concept)
                else:
                    self.inv_manager.registrar_salida(p_id, self.current_user_id, qty, state, concept)

                messagebox.showinfo("Éxito", "Stock actualizado correctamente")
                self.cargar_datos() 
                modal.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Dato inválido: {e}")

        tk.Button(modal, text="Confirmar Ajuste", bg=COLORS["primary"], fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=10, 
                  command=ejecutar_ajuste).pack(fill="x", pady=20)

    def abrir_modal_nuevo_producto(self) -> None:
        modal: Toplevel = Toplevel(self)
        modal.title("Nuevo Producto")
        modal.geometry("400x550")
        modal.configure(bg="white")
        modal.grab_set()

        tk.Label(modal, text="Agregar Producto", font=FONT_H2, bg="white", fg=COLORS["text_dark"]).pack(pady=15)
        form: tk.Frame = tk.Frame(modal, bg="white", padx=20)
        form.pack(fill="both", expand=True)

        entries: Dict[str, tk.Entry] = {}
        campos: List[Tuple[str, str]] = [
            ("Nombre del Producto", "name"), ("Código de Barras / SKU", "barcode"), 
            ("Categoría", "category"), ("Pasillo", "aisle"), ("Estante", "shelf"), ("Nivel", "level")
        ]

        for label, key in campos:
            tk.Label(form, text=label, bg="white", anchor="w", font=FONT_SMALL, fg=COLORS["text_gray"]).pack(fill="x", pady=(10, 0))
            e: tk.Entry = tk.Entry(form, bg="#F9FAFB", relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, font=FONT_BODY)
            e.pack(fill="x", ipady=5)
            entries[key] = e

        def guardar() -> None:
            name: str = entries["name"].get().strip()
            barcode: str = entries["barcode"].get().strip()
            if not name or not barcode:
                messagebox.showwarning("Atención", "Nombre y Código son obligatorios")
                return

            data: Tuple[str, str, str, str, str, str, str] = (
                name, barcode, entries["category"].get().strip() or "General",
                "Unidad", entries["aisle"].get().strip() or "0",
                entries["shelf"].get().strip() or "0", entries["level"].get().strip() or "0"
            )

            if insert_product(data):
                messagebox.showinfo("Éxito", f"Producto '{name}' registrado.")
                self.cargar_datos()
                modal.destroy()

        tk.Button(modal, text="Guardar Producto", bg=COLORS["primary"], fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", 
                  pady=10, command=guardar).pack(fill="x", padx=20, pady=25)