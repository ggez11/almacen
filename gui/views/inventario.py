import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from typing import Dict, List, Tuple, Any, Optional, Union

# Importaciones locales
from database.queries import get_all_products, insert_product
from gui.components.widgets import EntryWithPlaceholder
from services.inv_manager import InventoryManager, State # <--- Importación clave

# --- CONFIGURACIÓN DE COLORES Y ESTILOS ---
COLORS: Dict[str, str] = {
    "bg_main": "#F3F4F6",
    "primary": "#0D9488",
    "text_dark": "#111827",
    "text_gray": "#6B7280",
    "border": "#E5E7EB",
    "white": "#FFFFFF",
    "success_bg": "#D1FAE5", "success_fg": "#065F46",
    "warning_bg": "#FEF3C7", "warning_fg": "#92400E",
    "info_bg": "#DBEAFE",    "info_fg": "#1E40AF"
}

FONT_H2: Tuple[str, int, str] = ("Segoe UI", 12, "bold")
FONT_BODY: Tuple[str, int] = ("Segoe UI", 10)
FONT_SMALL: Tuple[str, int] = ("Segoe UI", 9)

class InventarioView(tk.Frame):
    def __init__(self, parent: tk.Widget, controller: Any = None) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])
        
        # El controller (MainSystem) nos provee el manager global
        # Si no existe, creamos uno local para evitar errores
        self.inv_manager: InventoryManager = getattr(controller, 'inv_manager', InventoryManager())
        self.current_user_id: int = getattr(controller, 'current_user_id', 1)

        self.main_area: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.main_area.pack(fill="both", expand=True)

        self.canvas: Optional[tk.Canvas] = None
        self.scrollable_frame: Optional[tk.Frame] = None

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

        header_frame: tk.Frame = tk.Frame(list_container, bg="white", height=50)
        header_frame.pack(fill="x", pady=5)
        
        headers: List[str] = ["PRODUCTO / SKU", "CANTIDAD", "UBICACIÓN", "ESTADO", "ACCIONES"]
        widths: List[int] = [35, 20, 15, 15, 15]

        for i, (text, w) in enumerate(zip(headers, widths)):
            header_frame.columnconfigure(i, weight=w)
            tk.Label(header_frame, text=text, font=("Segoe UI", 8, "bold"), 
                     fg=COLORS["text_gray"], bg="white", anchor="w").grid(row=0, column=i, sticky="we", padx=10, pady=15)

        self.canvas = tk.Canvas(list_container, bg="white", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=950)
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
            
            # Lógica visual de estado
            if stock > 50: status_info = ("Available", "success")
            elif stock > 0: status_info = ("Low Stock", "info")
            else: status_info = ("Out of Stock", "warning")

            self._crear_fila_producto(p_id, name, sku, stock, loc, status_info)

    def _crear_fila_producto(self, p_id: int, name: str, sku: str, stock: int, 
                             location: str, status_info: Tuple[str, str]) -> None:
        row: tk.Frame = tk.Frame(self.scrollable_frame, bg="white", pady=10)
        row.pack(fill="x", padx=5)
        for i in range(5): row.columnconfigure(i, weight=1)

        # 1. Producto
        f_prod: tk.Frame = tk.Frame(row, bg="white")
        f_prod.grid(row=0, column=0, sticky="w", padx=10)
        tk.Label(f_prod, text="📦", font=("Arial", 14), bg="#F3F4F6", width=3).pack(side="left", padx=(0,10))
        tk.Label(f_prod, text=name, font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w")
        tk.Label(f_prod, text=sku, font=FONT_SMALL, fg=COLORS["text_gray"], bg="white").pack(anchor="w")

        # 2. Cantidad
        tk.Label(row, text=f"{stock} Units", font=("Segoe UI", 9, "bold"), bg="white").grid(row=0, column=1, sticky="w", padx=10)

        # 3. Ubicación
        tk.Label(row, text=f"📍 {location}", font=FONT_SMALL, bg="#F3F4F6").grid(row=0, column=2, sticky="w", padx=10)

        # 4. Estado
        st_text, st_type = status_info
        colors_map = {"success": (COLORS["success_bg"], COLORS["success_fg"]), 
                      "warning": (COLORS["warning_bg"], COLORS["warning_fg"]),
                      "info": (COLORS["info_bg"], COLORS["info_fg"])}
        bg_st, fg_st = colors_map.get(st_type, ("#EEE", "#333"))
        
        lbl_st = tk.Label(row, text=st_text, font=("Segoe UI", 8, "bold"), bg=bg_st, fg=fg_st, padx=8)
        lbl_st.grid(row=0, column=3, sticky="w", padx=10)

        # 5. ACCIONES (Aquí usamos el InventoryManager)
        btn_ajuste = tk.Button(row, text="Adjust Stock", font=("Segoe UI", 8, "bold"), 
                               fg=COLORS["primary"], bg="white", relief="flat", cursor="hand2",
                               command=lambda: self._abrir_modal_ajuste(p_id, name))
        btn_ajuste.grid(row=0, column=4)

        tk.Frame(self.scrollable_frame, bg=COLORS["border"], height=1).pack(fill="x")

    def _abrir_modal_ajuste(self, p_id: int, p_name: str) -> None:
        """Modal para registrar Entradas o Salidas usando InventoryManager."""
        modal = Toplevel(self)
        modal.title("Stock Adjustment")
        modal.geometry("350x450")
        modal.configure(bg="white", padx=20, pady=20)
        modal.grab_set()

        tk.Label(modal, text=f"Ajustar: {p_name}", font=FONT_H2, bg="white", wraplength=300).pack(pady=(0, 20))

        # Formulario
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
                self.cargar_datos() # Refrescar tabla
                modal.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
            except Exception as e:
                messagebox.showerror("Error de Sistema", f"No se pudo realizar el ajuste: {e}")

        tk.Button(modal, text="Confirmar Ajuste", bg=COLORS["primary"], fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=10, 
                  command=ejecutar_ajuste).pack(fill="x", pady=20)

    def abrir_modal_nuevo_producto(self) -> None:
        """Abre una ventana emergente para registrar un nuevo producto en la base de datos."""
        modal: Toplevel = Toplevel(self)
        modal.title("Nuevo Producto")
        modal.geometry("400x600")
        modal.configure(bg="white")
        modal.transient(self)  # Se mantiene sobre la ventana principal
        modal.grab_set()       # Bloquea interacción con el fondo

        tk.Label(
            modal, text="Agregar Producto", 
            font=FONT_H2, bg="white", fg=COLORS["text_dark"]
        ).pack(pady=15)

        form: tk.Frame = tk.Frame(modal, bg="white", padx=20)
        form.pack(fill="both", expand=True)

        # Diccionario para almacenar las referencias a los widgets de entrada
        entries: Dict[str, tk.Entry] = {}
        
        # Definición de campos: (Label visible, llave en el diccionario)
        campos: List[Tuple[str, str]] = [
            ("Nombre del Producto", "name"), 
            ("Código de Barras / SKU", "barcode"), 
            ("Categoría", "category"), 
            ("Pasillo", "aisle"), 
            ("Estante", "shelf"), 
            ("Nivel", "level")
        ]

        for label, key in campos:
            tk.Label(
                form, text=label, bg="white", 
                anchor="w", font=FONT_SMALL, fg=COLORS["text_gray"]
            ).pack(fill="x", pady=(10, 0))
            
            e: tk.Entry = tk.Entry(
                form, bg="#F9FAFB", relief="flat", 
                highlightbackground=COLORS["border"], highlightthickness=1,
                font=FONT_BODY
            )
            e.pack(fill="x", ipady=5)
            entries[key] = e

        def guardar() -> None:
            """Extrae los datos, valida e inserta en la base de datos."""
            # Estructura de datos según requiere insert_product
            # (name, barcode, category, uom, aisle, shelf, level)
            try:
                name: str = entries["name"].get().strip()
                barcode: str = entries["barcode"].get().strip()
                category: str = entries["category"].get().strip()
                aisle: str = entries["aisle"].get().strip()
                shelf: str = entries["shelf"].get().strip()
                level: str = entries["level"].get().strip()

                if not name or not barcode:
                    messagebox.showwarning("Atención", "Nombre y Código son obligatorios")
                    return

                data: Tuple[str, str, str, str, str, str, str] = (
                    name,
                    barcode,
                    category or "General",
                    "Unidad",
                    aisle or "0",
                    shelf or "0",
                    level or "0"
                )

                resultado: Optional[int] = insert_product(data)
                
                if resultado:
                    messagebox.showinfo("Éxito", f"Producto '{name}' registrado correctamente.")
                    self.cargar_datos() # Refrescar la lista principal
                    modal.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo guardar el producto. Verifique si el código ya existe.")
            
            except Exception as e:
                messagebox.showerror("Error de Sistema", f"Ocurrió un error inesperado: {e}")

        # Botón de acción
        btn_save: tk.Button = tk.Button(
            modal, text="Guardar Producto", 
            bg=COLORS["primary"], fg="white", 
            font=("Segoe UI", 10, "bold"), relief="flat", 
            cursor="hand2", pady=10, command=guardar
        )
        btn_save.pack(fill="x", padx=20, pady=25)