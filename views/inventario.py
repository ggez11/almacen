import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from typing import Dict, List, Tuple, Any, Optional, Union

# Importaciones locales actualizadas
from database.queries import get_all_products, insert_product, buscar_producto_por_sku, obtener_ubicaciones, eliminar_producto, actualizar_producto
from services.inv_manager import InventoryManager
from services.auth_service import get_current_user

#Components
from gui.components.tooltip import ToolTip

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
    "info_bg": "#DBEAFE",    "info_fg": "#1E40AF",
    "error_bg": "#FEE2E2",   "error_fg": "#991B1B"
}

COLUMN_WEIGHTS: List[int] = [10, 4, 4, 6, 5, 6]

FONT_H2: Tuple[str, int, str] = ("Segoe UI", 12, "bold")
FONT_BODY: Tuple[str, int] = ("Segoe UI", 10)
FONT_SMALL: Tuple[str, int] = ("Segoe UI", 9)

class InventarioView(tk.Frame):
    def __init__(self, parent: tk.Widget, controller: Any = None) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])
        
        # Obtener usuario actual
        current_user = get_current_user()
        self.current_user_id = current_user.id if current_user else 1
        
        # Crear manager de inventario
        self.inv_manager = InventoryManager()
        
        # Almacenar productos para búsqueda rápida
        self.productos_cache: List[Dict[str, Any]] = []
        
        self.main_area: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.main_area.pack(fill="both", expand=True)

        self.canvas: Optional[tk.Canvas] = None
        self.scrollable_frame: Optional[tk.Frame] = None
        self.scrollbar_horizontal: Optional[ttk.Scrollbar] = None  # Nueva barra horizontal

        self._construir_topbar()
        self._construir_lista_productos()

    def _construir_topbar(self) -> None:
        top_frame: tk.Frame = tk.Frame(self.main_area, bg=COLORS["bg_main"], pady=20, padx=30)
        top_frame.pack(fill="x")

        # Búsqueda mejorada para SKU
        search_container: tk.Frame = tk.Frame(top_frame, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        search_container.pack(side="left", ipady=5, ipadx=5)
        
        tk.Label(search_container, text="🔍", bg="white", fg=COLORS["text_gray"]).pack(side="left", padx=5)
        
        self.entry_search: tk.Entry = tk.Entry(
            search_container, 
            bg="white", bd=0, font=FONT_BODY, width=30, fg=COLORS["text_dark"]
        )
        self.entry_search.pack(side="left")
        self.entry_search.insert(0, "Buscar por SKU, Nombre...")
        self.entry_search.bind("<FocusIn>", self._on_search_focus_in)
        self.entry_search.bind("<FocusOut>", self._on_search_focus_out)
        self.entry_search.bind("<KeyRelease>", self._on_search_key_release)
        
        # Botón de búsqueda rápida por SKU
        tk.Button(search_container, text="SKU", bg=COLORS["primary"], fg="white",
                  font=("Segoe UI", 8, "bold"), relief="flat", padx=8, pady=2,
                  cursor="hand2", command=self.busqueda_sku_rapida).pack(side="right", padx=(5, 0))

        # Botón para nuevo producto
        tk.Button(top_frame, text="＋ Add Product", bg=COLORS["primary"], fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=5, 
                  cursor="hand2", command=self.abrir_modal_nuevo_producto).pack(side="right")

        # Botón para actualizar
        tk.Button(top_frame, text="🔄 Actualizar", bg=COLORS["border"], fg=COLORS["text_dark"],
                  font=("Segoe UI", 9), relief="flat", padx=10, pady=5,
                  cursor="hand2", command=self.cargar_datos).pack(side="right", padx=5)

    def _construir_lista_productos(self) -> None:
        list_container: tk.Frame = tk.Frame(self.main_area, bg="white")
        list_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        list_container.bind("<Enter>", lambda _: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        list_container.bind("<Leave>", lambda _: self.canvas.unbind_all("<MouseWheel>"))

        # Encabezados de la tabla CON PRECIO
        header_frame: tk.Frame = tk.Frame(list_container, bg="white")
        header_frame.pack(fill="x", pady=5)
        
        # Cambiado: añadida columna "PRECIO" entre "CANTIDAD" y "UBICACIÓN"
        headers: List[str] = ["PRODUCTO / SKU", "STOCK", "PRECIO", "UBICACIÓN", "ESTADO", "ACCIONES"]
        for i, (text, w) in enumerate(zip(headers, COLUMN_WEIGHTS)):
            header_frame.columnconfigure(i, weight=w, uniform="table_col")
            tk.Label(header_frame, text=text, font=("Segoe UI", 8, "bold"), 
                     fg=COLORS["text_gray"], bg="white", anchor="w").grid(row=0, column=i, sticky="we", padx=10, pady=15)

        # Contenedor para canvas y scrollbars
        table_container = tk.Frame(list_container, bg="white")
        table_container.pack(fill="both", expand=True)
        
        # Scrollbar horizontal NUEVA
        self.scrollbar_horizontal = ttk.Scrollbar(table_container, orient="horizontal")
        
        # Canvas con scrollbar vertical
        self.canvas = tk.Canvas(table_container, bg="white", highlightthickness=0,
                                xscrollcommand=self.scrollbar_horizontal.set)
        
        scrollbar_vertical = ttk.Scrollbar(table_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        ))
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar_vertical.set)
        self.scrollbar_horizontal.configure(command=self.canvas.xview)
        
        # Empaquetar widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar_vertical.pack(side="right", fill="y")
        self.scrollbar_horizontal.pack(side="bottom", fill="x")
        
        # Configurar scroll horizontal
        self._configurar_scroll_horizontal()
        
        self.cargar_datos()

    def _configurar_scroll_horizontal(self) -> None:
        """Configura el comportamiento del scroll horizontal."""
        def on_frame_configure(event):
            # Actualizar scrollregion cuando el frame cambia de tamaño
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        def on_canvas_configure(event):
            # Ajustar el ancho del frame interior al del canvas
            canvas_width = event.width
            self.canvas.itemconfig("all", width=canvas_width)
        
        self.scrollable_frame.bind("<Configure>", on_frame_configure)
        self.canvas.bind("<Configure>", on_canvas_configure)

    def cargar_datos(self, filtro: str = "") -> None:
        """Carga los productos desde la base de datos con filtro opcional."""
        if not self.scrollable_frame:
            return
            
        # Limpiar frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            # Obtener productos
            productos: List[Tuple[Any, ...]] = get_all_products()
            self.productos_cache = []
            
            for p in productos:
                # Estructura de get_all_products(): (id, name, sku, category, stock, location, precio, proveedor, estado)
                producto_dict = {
                    'id': p[0],
                    'nombre': p[1],
                    'sku': p[2],
                    'categoria': p[3],
                    'stock': p[4],
                    'unidad_medida': p[5],
                    'ubicacion': p[6],
                    'precio': float(p[7]) if p[7] else 0.0,  # Convertir a float
                    'proveedor': p[8],
                    'estado': p[9]
                }
                self.productos_cache.append(producto_dict)
                
                # Aplicar filtro si existe
                if filtro:
                    filtro_lower = filtro.lower()
                    sku_match = filtro_lower in str(producto_dict['sku']).lower()
                    nombre_match = filtro_lower in str(producto_dict['nombre']).lower()
                    if not (sku_match or nombre_match):
                        continue
                    
                # Crear fila
                self._crear_fila_producto(producto_dict)

        except Exception as e:
            print(f"Error al cargar productos: {e}")
            tk.Label(self.scrollable_frame, text="Error al cargar productos", 
                    font=FONT_BODY, fg=COLORS["error_fg"], bg="white").pack(pady=50)
            return

        # Si no hay productos
        if not self.scrollable_frame.winfo_children():
            tk.Label(self.scrollable_frame, text="No hay productos registrados", 
                    font=FONT_BODY, fg=COLORS["text_gray"], bg="white").pack(pady=50)

    def _crear_fila_producto(self, producto: Dict[str, Any]) -> None:
        """Crea una fila en la tabla para un producto."""
        row: tk.Frame = tk.Frame(self.scrollable_frame, bg="white", pady=10)
        row.pack(fill="x")
        
        # Configurar columnas (6 columnas ahora con PRECIO)
        for i, weight in enumerate(COLUMN_WEIGHTS):
            row.columnconfigure(i, weight=weight, uniform="table_col")

        # 1. Producto y SKU
        f_prod: tk.Frame = tk.Frame(row, bg="white")
        f_prod.grid(row=0, column=0, sticky="w", padx=10)

        tk.Label(f_prod, text="📦", font=("Arial", 14), bg="#F3F4F6", width=3).grid(row=0, column=0, padx=10)

        nombre_display = producto['nombre']
        if len(nombre_display) > 25:
            nombre_display = nombre_display[:22] + "..."
            
        lbl_name: tk.Label = tk.Label(f_prod, text=nombre_display, font=("Segoe UI", 9, "bold"), bg="white", anchor="w", justify="left", width=25)
        lbl_name.grid(row=0, column=1, sticky="we")

        if len(nombre_display) > 22: 
            ToolTip(lbl_name, nombre_display)

        tk.Label(f_prod, text=producto['sku'], font=FONT_SMALL, fg=COLORS["text_gray"], bg="white").grid(row=1, column=1, sticky="w")

        # 2. Cantidad
        stock = producto['stock']
        unidad_medida = producto['unidad_medida']
        tk.Label(row, text=f"{stock} {unidad_medida}", font=("Segoe UI", 9, "bold"), bg="white", anchor="center", justify="left").grid(row=0, column=1, sticky="we", padx=10)

        # 3. PRECIO
        precio = producto['precio']
        precio_text = f"${precio:.2f}" if precio > 0 else "$0.00"
        tk.Label(row, text=precio_text, font=("Segoe UI", 9, "bold"), bg="white", anchor="center", justify="left").grid(row=0, column=2, sticky="we", padx=10)

        # 4. Ubicación
        ubicacion = producto['ubicacion'] or "Sin ubicación"
        tk.Label(row, text=f"📍 {ubicacion}", font=FONT_SMALL, bg="#F3F4F6", anchor="w", justify="center").grid(row=0, column=3, sticky="we", padx=10)

        # 5. Estado
        estado = producto['estado']
        estado_colors = {
            "In Stock": (COLORS["success_bg"], COLORS["success_fg"]),
            "Low Stock": (COLORS["warning_bg"], COLORS["warning_fg"]),
            "Out of Stock": (COLORS["error_bg"], COLORS["error_fg"])
        }
        
        bg_st, fg_st = estado_colors.get(estado, (COLORS["info_bg"], COLORS["info_fg"]))
        
        lbl_st = tk.Label(row, text=estado, font=("Segoe UI", 8, "bold"), anchor="w", justify="center", bg=bg_st, fg=fg_st, padx=8)
        lbl_st.grid(row=0, column=4, sticky="we", padx=10)

        # 6. ACCIONES
        btn_frame = tk.Frame(row, bg="white")
        btn_frame.grid(row=0, column=5, sticky="we", padx=10)
        
        # # Botón Adjust Stock
        # btn_ajuste = tk.Button(btn_frame, text="Adjust Stock", font=("Segoe UI", 8, "bold"), 
        #                        fg=COLORS["primary"], bg="white", relief="flat", cursor="hand2",
        #                        command=lambda pid=producto['id'], pname=producto['nombre']: self._abrir_modal_ajuste(pid, pname))
        # btn_ajuste.pack(side="left", padx=2)

        # Botón Ajustar
        tk.Button(btn_frame, text="📊", font=("Segoe UI", 14), fg=COLORS["primary"], bg="white",
                  relief="flat", cursor="hand2", command=lambda: self._abrir_modal_ajuste(producto['id'], producto['nombre'])).grid(row=0, column=6, sticky="w")

        # Botón Editar
        tk.Button(btn_frame, text="ᴇᴅɪᴛ", font=("Segoe UI", 14), fg="#2563EB", bg="white", width=3,
                  relief="flat", cursor="hand2", command=lambda: self.abrir_modal_editar_producto(producto['id'], producto['nombre'], producto['sku'], producto['categoria'], producto['ubicacion'])).grid(row=0, column=7, sticky="e")

        # Botón Eliminar
        tk.Button(btn_frame, text="ᴅᴇʟ", font=("Segoe UI", 14), fg="#DC2626", bg="white", width=3,
                  relief="flat", cursor="hand2", command=lambda: self.confirmar_eliminacion(producto['id'], producto['nombre'])).grid(row=0, column=8, sticky="e")
        
        # Botón View Details (solo si es admin)
        current_user = get_current_user()
        if current_user and current_user.role == 'Administrador':
            btn_detalles = tk.Button(btn_frame, text="☰", font=("Segoe UI", 14),
                                    fg=COLORS["primary"], bg="white", relief="flat", cursor="hand2",
                                    command=lambda pid=producto['id']: self._ver_detalles(pid))
            btn_detalles.grid(row=0, column=9, sticky="w")

        # Separador
        tk.Frame(self.scrollable_frame, bg=COLORS["border"], height=1).pack(fill="x")

    def confirmar_eliminacion(self, p_id: int, name: str) -> None:
        if messagebox.askyesno("Confirmar", f"¿Eliminar definitivamente '{name}'?"):
            if eliminar_producto(p_id):
                self.cargar_datos() # Re-dibuja la tabla
                messagebox.showinfo("✅ Éxito", f"Producto '{name}' eliminado.")

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
            data: dict[str, Any] = {
                "nombre": entries["name"].get().strip(),
                "sku": entries["barcode"].get().strip(),
                "categoria": entries["category"].get().strip(),
                "ubicacion": entries["location"].get().strip()
            }
            if actualizar_producto(p_id, data):
                messagebox.showinfo("Éxito", "Producto actualizado")
                self.cargar_datos()
                modal.destroy()

        tk.Button(modal, text="Guardar Cambios", bg=COLORS["primary"], fg="white", font=("Segoe UI", 10, "bold"), 
                  relief="flat", pady=10, command=actualizar).pack(fill="x", padx=20, pady=25)

    def _abrir_modal_ajuste(self, p_id: int, p_name: str) -> None:
        """Modal para ajustar stock usando el nuevo InventoryManager."""
        modal = Toplevel(self)
        modal.title(f"Ajustar Stock: {p_name}")
        modal.geometry("400x500")
        modal.configure(bg="white", padx=20, pady=20)
        modal.grab_set()

        tk.Label(modal, text=f"{p_name}", font=FONT_H2, bg="white", wraplength=300).pack(pady=(0, 20))

        # Tipo de ajuste
        tk.Label(modal, text="Tipo de Ajuste", bg="white", font=FONT_SMALL, fg=COLORS["text_gray"]).pack(anchor="center")
        combo_tipo = ttk.Combobox(modal, values=["Entrada (IN)", "Salida (OUT)", "Ajuste Manual"], state="readonly", font=FONT_SMALL)
        combo_tipo.pack(fill="x", pady=5)
        combo_tipo.set("Entrada (IN)")

        # Razón del ajuste
        tk.Label(modal, text="Razón", bg="white", font=FONT_SMALL, fg=COLORS["text_gray"]).pack(anchor="center", pady=(10, 0))
        combo_razon = ttk.Combobox(modal, values=["recepcion", "venta", "ajuste manual", "dañado", 
                                                  "vencido", "robo", "uso interno", "transferencia"], 
                                        state="readonly", font=FONT_SMALL)
        combo_razon.pack(fill="x", pady=5)
        combo_razon.set("ajuste manual")

        # Cantidad
        tk.Label(modal, text="Cantidad", bg="white", font=FONT_SMALL, fg=COLORS["text_gray"]).pack(anchor="center", pady=(10, 0))
        entry_qty = tk.Entry(modal, font=FONT_BODY, bg="#F9FAFB", relief="flat", highlightthickness=1)
        entry_qty.pack(fill="x", pady=5)
        entry_qty.insert(0, "0")

        # Ubicación (si hay múltiples)
        tk.Label(modal, text="Ubicación", bg="white", font=FONT_SMALL, fg=COLORS["text_gray"]).pack(anchor="center", pady=(10, 0))
        ubicaciones = obtener_ubicaciones()
        ubicacion_options = [f"{ub[1]} (ID: {ub[0]})" for ub in ubicaciones] if ubicaciones else ["Predeterminada"]
        
        combo_ubicacion = ttk.Combobox(modal, values=ubicacion_options, state="readonly", font=FONT_SMALL)
        combo_ubicacion.pack(fill="x", pady=5)
        if ubicacion_options:
            combo_ubicacion.set(ubicacion_options[0])

        # Detalle adicional
        tk.Label(modal, text="Detalle (OPCIONAL)", bg="white", font=FONT_SMALL, fg=COLORS["text_gray"]).pack(anchor="center", pady=(10, 0))
        entry_detalle = tk.Entry(modal, font=FONT_BODY, bg="#F9FAFB", relief="flat", highlightthickness=1)
        entry_detalle.pack(fill="x", pady=5)

        def ejecutar_ajuste() -> None:
            try:
                tipo_str = combo_tipo.get()
                razon = combo_razon.get()
                cantidad = int(entry_qty.get())
                detalle = entry_detalle.get()
                
                if cantidad <= 0:
                    messagebox.showwarning("Error", "La cantidad debe ser mayor a 0")
                    return

                # Obtener ID de ubicación
                ubicacion_id = None
                if ubicaciones and combo_ubicacion.get():
                    ubicacion_str = combo_ubicacion.get()
                    # Extraer ID de la cadena "Código (ID: X)"
                    if "(ID:" in ubicacion_str:
                        ubicacion_id = int(ubicacion_str.split("(ID:")[1].strip()[:-1])
                    else:
                        # Si no tiene formato con ID, usar la primera ubicación
                        ubicacion_id = ubicaciones[0][0] if ubicaciones else None

                # Ejecutar según tipo
                if tipo_str == "Entrada (IN)":
                    self.inv_manager.registrar_entrada(
                        product_id=p_id,
                        quantity=cantidad,
                        razon=razon,
                        ubicacion_id=ubicacion_id,
                        razon_detalle=detalle,
                        user_id=self.current_user_id
                    )
                    
                elif tipo_str == "Salida (OUT)":
                    self.inv_manager.registrar_salida(
                        product_id=p_id,
                        quantity=cantidad,
                        razon=razon,
                        ubicacion_id=ubicacion_id,
                        razon_detalle=detalle,
                        user_id=self.current_user_id
                    )
                    
                else:  # Ajuste Manual
                    self.inv_manager.ajuste_manual(
                        product_id=p_id,
                        cantidad_nueva=cantidad,
                        ubicacion_id=ubicacion_id,
                        razon_detalle=detalle,
                        user_id=self.current_user_id
                    )

                messagebox.showinfo("✅ Éxito", "Stock actualizado correctamente")
                self.cargar_datos()  # Refrescar tabla
                modal.destroy()
                
            except ValueError as e:
                messagebox.showerror("❌ Error de Validación", str(e))
            except Exception as e:
                messagebox.showerror("❌ Error del Sistema", f"No se pudo realizar el ajuste:\n\n{str(e)}")

        # Botones
        btn_frame = tk.Frame(modal, bg="white")
        btn_frame.pack(fill="x", pady=20)
        
        tk.Button(btn_frame, text="✖ Cancelar", bg=COLORS["border"], fg=COLORS["text_dark"],
                  font=FONT_BODY, relief="flat", padx=20, pady=8,
                  command=modal.destroy).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="✅ Confirmar Ajuste", bg=COLORS["primary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=8,
                  command=ejecutar_ajuste).pack(side="right", padx=5)

    def _ver_detalles(self, producto_id: int) -> None:
        """Muestra los detalles de un producto."""
        # Buscar producto en cache
        producto = None
        for p in self.productos_cache:
            if p['id'] == producto_id:
                producto = p
                break
        
        if not producto:
            messagebox.showwarning("Producto no encontrado", "El producto no existe o ha sido eliminado.")
            return
            
        # Crear ventana de detalles
        modal = Toplevel(self)
        modal.title(f"📦 Detalles: {producto['nombre']}")
        modal.geometry("450x350")
        modal.configure(bg="white", padx=25, pady=25)
        modal.resizable(False, False)
        
        # Título
        tk.Label(modal, text=f"📦 {producto['nombre']}", font=FONT_H2, bg="white").pack(anchor="w")
        tk.Label(modal, text=f"SKU: {producto['sku']}", font=FONT_BODY, bg="white").pack(anchor="w", pady=(0, 15))
        
        # Mostrar información
        info_frame = tk.Frame(modal, bg="white")
        info_frame.pack(fill="both", expand=True, pady=10)
        
        detalles = [
            ("Categoría:", producto['categoria'] or "No especificada"),
            ("Stock Actual:", f"{producto['stock']} unidades"),
            ("Ubicación:", producto['ubicacion'] or "No asignada"),
            ("Precio:", f"${producto['precio']:.2f}" if producto['precio'] else "No definido"),
            ("Proveedor:", producto['proveedor'] or "No especificado"),
            ("Estado:", producto['estado'])
        ]
        
        for label, valor in detalles:
            row = tk.Frame(info_frame, bg="white")
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, font=FONT_SMALL, fg=COLORS["text_gray"], 
                    bg="white", width=12, anchor="w").pack(side="left")
            tk.Label(row, text=valor, font=FONT_SMALL, fg=COLORS["text_dark"], 
                    bg="white", anchor="w").pack(side="left", padx=10)
        
        # Botón cerrar
        tk.Button(modal, text="Cerrar", bg=COLORS["border"], fg=COLORS["text_dark"],
                  font=FONT_BODY, relief="flat", padx=30, pady=8,
                  command=modal.destroy).pack(pady=(20, 0))

    def abrir_modal_nuevo_producto(self) -> None:
        """Abre ventana para registrar un nuevo producto CON SCROLL Y BOTONES FIJOS"""
        modal = tk.Toplevel(self)
        modal.title("➕ Nuevo Producto")
        modal.geometry("500x650")
        modal.configure(bg="white")
        modal.resizable(False, True)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        
        # Centrar ventana
        modal.update_idletasks()
        width = modal.winfo_width()
        height = modal.winfo_height()
        x = (modal.winfo_screenwidth() // 2) - (width // 2)
        y = (modal.winfo_screenheight() // 2) - (height // 2) - 50
        modal.geometry(f'{width}x{height}+{x}+{y}')
        
        # ========== PARTE SUPERIOR: TÍTULO ==========
        header_frame = tk.Frame(modal, bg=COLORS["primary"], height=80)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="➕ NUEVO PRODUCTO",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["primary"],
            fg="white"
        ).pack(expand=True, pady=(15, 5))
        
        tk.Label(
            header_frame,
            text="Complete los campos obligatorios (*)",
            font=("Segoe UI", 9),
            bg=COLORS["primary"],
            fg="#E0F2FE"
        ).pack(pady=(0, 10))
        
        # ========== PARTE CENTRAL: FORMULARIO CON SCROLL ==========
        main_container = tk.Frame(modal, bg="white")
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Canvas con scrollbar
        canvas = tk.Canvas(main_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        # Frame scrollable
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=480)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(25, 5))
        scrollbar.pack(side="right", fill="y", padx=(0, 20))
        
        # Contenido del formulario
        form_frame = tk.Frame(scrollable_frame, bg="white", padx=5, pady=15)
        form_frame.pack(fill="both", expand=True, padx=10)
        
        entries = {}
        row = 0
        
        # Campos - AÑADIDO PRECIO como obligatorio
        campos = [
            ("Nombre del Producto *", "nombre", "text", ""),
            ("Código de Barras / SKU *", "sku", "text", ""),
            ("Categoría", "categoria", "text", "General"),
            ("Precio de Venta *", "precio", "number", ""),
            ("Proveedor", "proveedor", "text", ""),
            ("Unidad de Medida", "unidad", "combo", "Units"),
            ("Stock Mínimo", "stock_min", "number", "0"),
            ("Ubicación", "ubicacion", "text", "Almacén Principal")
        ]
        
        for label_text, key, field_type, default in campos:
            field_frame = tk.Frame(form_frame, bg="white")
            field_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
            field_frame.columnconfigure(0, weight=1)
            
            # Label
            label_color = COLORS["primary"] if "*" in label_text else COLORS["text_dark"]
            tk.Label(
                field_frame,
                text=label_text,
                bg="white",
                anchor="w",
                font=("Segoe UI", 10, "bold"),
                fg=label_color
            ).grid(row=0, column=0, sticky="w", pady=(0, 6))
            
            # Field
            if field_type == "combo":
                combo = ttk.Combobox(
                    field_frame,
                    values=["Units", "Cajas", "Paquetes", "Litros", "Kilogramos"],
                    state="readonly",
                    font=("Segoe UI", 11)
                )
                combo.grid(row=1, column=0, sticky="ew", ipady=8)
                combo.set(default)
                entries[key] = combo
                
            else:
                entry = tk.Entry(
                    field_frame,
                    bg="#F9FAFB",
                    relief="solid",
                    font=("Segoe UI", 11),
                    borderwidth=1,
                    highlightthickness=0,
                    width=30
                )
                entry.grid(row=1, column=0, sticky="ew", ipady=8)
                
                if default:
                    entry.insert(0, default)
                    if default == "General" or default == "Almacén Principal":
                        entry.config(fg=COLORS["text_gray"])
                
                entries[key] = entry
            
            row += 1
        
        # Espacio extra
        tk.Frame(scrollable_frame, bg="white", height=20).pack()
        
        # ========== PARTE INFERIOR: BOTONES FIJOS ==========
        button_container = tk.Frame(modal, bg="white", height=90)
        button_container.pack(side="bottom", fill="x", padx=25, pady=(0, 20))
        button_container.pack_propagate(False)
        
        button_frame = tk.Frame(button_container, bg="white")
        button_frame.pack(expand=True)
        
        # Función GUARDAR
        def guardar_producto() -> None:
            try:
                # 1. Recuperar y limpiar datos
                nombre: str = entries["nombre"].get().strip()
                sku: str = entries["sku"].get().strip()
                precio_str: str = entries["precio"].get().strip()
                
                # 2. Validaciones de interfaz
                if not nombre or not sku or not precio_str:
                    messagebox.showwarning("❌ Error", "Complete los campos obligatorios (*)")
                    return

                try:
                    precio: float = float(precio_str)
                    stock_min_str: str = entries["stock_min"].get().strip()
                    cantidad_inicial: int = int(stock_min_str) if stock_min_str else 0
                    if precio <= 0: raise ValueError
                except ValueError:
                    messagebox.showwarning("❌ Error", "Valores numéricos inválidos")
                    return

                # 3. Preparar datos
                categoria: str = entries["categoria"].get().strip() or "General"
                proveedor: str = entries["proveedor"].get().strip() or ""
                unidad: str = entries["unidad"].get()
                ubicacion: str = entries["ubicacion"].get().strip() or "Almacén Principal"

                datos_producto: tuple = (
                    nombre, sku, categoria, precio, 
                    proveedor, unidad, cantidad_inicial, ubicacion
                )

                # 4. Intento de inserción (Lógica de Negocio)
                # Aquí manejamos el posible SKU duplicado según lo que devuelve tu insert_product
                producto_id: Optional[int] = insert_product(datos_producto)

                if producto_id is None:
                    # Si insert_product devolvió None es porque falló el SKU (según tu execute_query)
                    messagebox.showerror("❌ SKU Duplicado", f"El código '{sku}' ya existe.")
                    entries["sku"].focus_set()
                    entries["sku"].selection_range(0, tk.END)
                    return

                # 5. Registro de Inventario (Solo si se creó el producto)
                if cantidad_inicial > 0:
                    try:
                        self.inv_manager.registrar_entrada(
                            product_id=producto_id,
                            quantity=cantidad_inicial,
                            razon="ajuste manual",
                            razon_detalle="Carga inicial de producto nuevo"
                        )
                    except Exception as e_inv:
                        # No detenemos el proceso si el producto se creó pero el stock falló
                        print(f"Aviso: Producto {producto_id} creado pero falló stock: {e_inv}")

                # 6. Éxito final
                messagebox.showinfo(
                        "✅ Éxito",
                        f"Producto creado exitosamente!\n\n"
                        f"📦 Nombre: {nombre}\n"
                        f"🔢 SKU: {sku}\n"
                        f"💰 Precio: ${precio:.2f}\n"
                        f"📍 Ubicación: {ubicacion}"
                    )
                
                self.cargar_datos() # Refrescar tabla de la vista principal
                unbind_mousewheel()
                modal.destroy()

            except Exception as e:
                # Captura cualquier error no controlado
                error_msg: str = str(e)
                if "UNIQUE constraint failed" in error_msg:
                    messagebox.showerror("❌ Error", "El SKU ya existe.")
                    entries["sku"].focus_set()
                else:
                    messagebox.showerror("❌ Error Inesperado", f"Ocurrió un error: {error_msg}")
                
        # Botón Cancelar
        btn_cancelar = tk.Button(
            button_frame,
            text="✖ CANCELAR",
            bg="#E5E7EB",
            fg=COLORS["text_dark"],
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            width=12,
            height=1,
            cursor="hand2",
            command=modal.destroy
        )
        btn_cancelar.pack(side="left", padx=(0, 15))
        
        # Botón Guardar
        btn_guardar = tk.Button(
            button_frame,
            text="💾 GUARDAR PRODUCTO",
            bg=COLORS["primary"],
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            width=20,
            height=1,
            cursor="hand2",
            command=guardar_producto
        )
        btn_guardar.pack(side="right")
                
                # ========== CONFIGURACIONES FINALES ==========
                # Scroll con rueda del mouse
        def _on_mousewheel(event):
            """Maneja el scroll del mouse de forma segura."""
            try:
                # Verificar si el canvas todavía existe
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                pass  # Ignorar errores si el widget ya fue destruido

        # Guardar referencia para poder desvincular después
        def bind_mousewheel():
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def unbind_mousewheel():
            try:
                modal.unbind_all("<MouseWheel>")
            except:
                pass

        # Vincular cuando se crea
        bind_mousewheel()
        
        # Enfocar primer campo
        entries["nombre"].focus_set()
        
        # Atajos de teclado
        modal.bind('<Return>', lambda e: guardar_producto())
        modal.bind('<Escape>', lambda e: modal.destroy())
        
        # Ajustar scroll
        modal.update()
        canvas.config(scrollregion=canvas.bbox("all"))
        modal.protocol("WM_DELETE_WINDOW", lambda: [unbind_mousewheel(), modal.destroy()])
        return modal
    
    # Métodos para búsqueda
    def _on_search_focus_in(self, event=None) -> None:
        if self.entry_search.get() == "Buscar por SKU, Nombre...":
            self.entry_search.delete(0, tk.END)
            self.entry_search.config(fg=COLORS["text_dark"])

    def _on_search_focus_out(self, event=None) -> None:
        if not self.entry_search.get():
            self.entry_search.insert(0, "Buscar por SKU, Nombre...")
            self.entry_search.config(fg=COLORS["text_gray"])

    def _on_search_key_release(self, event=None) -> None:
        filtro = self.entry_search.get()
        if filtro != "Buscar por SKU, Nombre...":
            self.cargar_datos(filtro)
    
    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.canvas:
            # En Windows es event.delta, en Linux suele ser event.num
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # NUEVO: Búsqueda por SKU
    def busqueda_sku_rapida(self) -> None:
        """Realiza una búsqueda específica por SKU."""
        sku_busqueda = self.entry_search.get()
        if not sku_busqueda or sku_busqueda == "Buscar por SKU, Nombre...":
            messagebox.showinfo("Búsqueda por SKU", "Ingrese un SKU para buscar")
            return
        
        # Usar la función de queries para buscar por SKU
        from database.queries import buscar_producto_por_sku
        producto = buscar_producto_por_sku(sku_busqueda)
        
        if producto:
            # Limpiar la vista
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            # Mostrar el producto encontrado
            producto_dict = {
                'id': producto['id'],
                'nombre': producto['nombre'],
                'sku': producto['sku'],
                'categoria': producto['categoria'],
                'stock': producto['stock_actual'],
                'ubicacion': producto['ubicacion'],
                'precio': producto['precio'],
                'proveedor': producto['proveedor'],
                'estado': 'In Stock' if producto['stock_actual'] > 0 else 'Out of Stock'
            }
            self._crear_fila_producto(producto_dict)
            
            # Mostrar mensaje
            tk.Label(self.scrollable_frame, text=f"✔ Producto encontrado: {producto['nombre']}", 
                    font=FONT_SMALL, fg=COLORS["success_fg"], bg="white").pack(pady=10)
        else:
            messagebox.showinfo("Búsqueda por SKU", f"No se encontró ningún producto con SKU: {sku_busqueda}")
            self.cargar_datos()  # Restaurar vista normal
