import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple, Union, Optional

# Importaciones del sistema
from database.queries import get_all_products, crear_orden_venta
from services.auth_service import get_current_user
from services.inv_manager import InventoryManager

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
    "danger": "#EF4444",
    "success_bg": "#D1FAE5", "success_fg": "#065F46",
    "warning_bg": "#FEF3C7", "warning_fg": "#92400E",
    "error_bg": "#FEE2E2", "error_fg": "#991B1B"
}

FontTuple = Tuple[str, int, str]

COLUMN_WEIGHTS: List[int] = [3, 3, 3, 3, 3, 3]

class EnviosView(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.configure(bg=COLORS["bg_main"])

        # Obtener usuario actual
        self.current_user = get_current_user()
        self.user_id = self.current_user.id if self.current_user else 1

        self.inv_manager = InventoryManager()

        # Estado del carrito: Lista de diccionarios
        self.cart_items: List[Dict[str, Union[str, int, float]]] = []

        # Estructura Principal: Panel Izquierdo (Productos) | Panel Derecho (Carrito)
        self.left_panel: tk.Frame = tk.Frame(self, bg=COLORS["bg_main"])
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)

        self.right_panel: tk.Frame = tk.Frame(self, bg=COLORS["bg_panel"], width=400, 
                                              highlightbackground=COLORS["border"], highlightthickness=1)
        self.right_panel.pack(side="right", fill="y", padx=(10, 20), pady=20)
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

        # Título
        tk.Label(top_bar, text="📦 SELECCIONAR PRODUCTOS", 
                font=("Segoe UI", 12, "bold"), bg=COLORS["bg_main"], 
                fg=COLORS["primary"]).pack(side="left", padx=(0, 20))

        search_cont: tk.Frame = tk.Frame(top_bar, bg="white", 
                                         highlightbackground=COLORS["border"], 
                                         highlightthickness=1)
        search_cont.pack(side="left", fill="x", expand=True, ipady=5)

        tk.Label(search_cont, text="🔍", bg="white", fg=COLORS["text_gray"]).pack(side="left", padx=5)
        
        self.entry_search: tk.Entry = tk.Entry(
            search_cont, 
            bg="white", 
            bd=0, 
            font=("Segoe UI", 10),
            width=40
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_search.insert(0, "Buscar por SKU o nombre...")
        self.entry_search.bind("<FocusIn>", self._on_search_focus_in)
        self.entry_search.bind("<FocusOut>", self._on_search_focus_out)
        self.entry_search.bind("<KeyRelease>", self._on_search_key_release)

        # Botón actualizar
        tk.Button(top_bar, text="🔄 Actualizar", bg=COLORS["border"], fg=COLORS["text_dark"],
                  font=("Segoe UI", 9), relief="flat", padx=10, pady=5,
                  cursor="hand2", command=self.cargar_productos).pack(side="right", padx=5)

        # --- Cabecera de la Tabla ---
        headers: List[str] = ["PRODUCTO", "SKU", "STOCK", "PRECIO", "UBICACIÓN", "ACCIÓN"]
        
        head_fr: tk.Frame = tk.Frame(self.left_panel, bg=COLORS["bg_main"])
        head_fr.pack(fill="x", pady=5)
        
        # Configurar grid para cabeceras
        for i, text in enumerate(headers):
            head_fr.columnconfigure(i, weight=COLUMN_WEIGHTS[i], uniform="table_col")
            tk.Label(head_fr, text=text, font=("Segoe UI", 8, "bold"), 
                     bg=COLORS["bg_main"], fg=COLORS["text_gray"], anchor="w").grid(
                         row=0, column=i, sticky="we", padx=5)

        # --- CONTENEDOR PRINCIPAL CON SCROLL VERTICAL Y HORIZONTAL ---
        main_container = tk.Frame(self.left_panel, bg=COLORS["bg_main"])
        main_container.pack(fill="both", expand=True)
        
        # Canvas principal
        self.canvas_prod = tk.Canvas(main_container, bg=COLORS["bg_main"], highlightthickness=0)
        
        # Scrollbar vertical
        self.scroll_prod_vertical = ttk.Scrollbar(main_container, orient="vertical", command=self.canvas_prod.yview)
        
        # Scrollbar horizontal NUEVO
        self.scroll_prod_horizontal = ttk.Scrollbar(main_container, orient="horizontal", command=self.canvas_prod.xview)
        
        # Frame contenedor (scrollable)
        self.frame_list = tk.Frame(self.canvas_prod, bg=COLORS["bg_main"])
        
        # Configurar scroll
        def configurar_scrollregion(e):
            self.canvas_prod.configure(scrollregion=self.canvas_prod.bbox("all"))
        
        self.frame_list.bind("<Configure>", configurar_scrollregion)
        
        # Crear ventana en canvas
        self.canvas_prod.create_window((0, 0), window=self.frame_list, anchor="nw")
        
        # Configurar scrollbars
        self.canvas_prod.configure(
            yscrollcommand=self.scroll_prod_vertical.set,
            xscrollcommand=self.scroll_prod_horizontal.set
        )
        
        # Posicionar widgets con grid para mejor control
        self.canvas_prod.grid(row=0, column=0, sticky="nsew")
        self.scroll_prod_vertical.grid(row=0, column=1, sticky="ns")
        self.scroll_prod_horizontal.grid(row=1, column=0, sticky="ew", columnspan=2)
        
        # Configurar expansión
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Ajustar tamaño de la ventana en canvas cuando el canvas cambie de tamaño
        def ajustar_ventana_canvas(event):
            self.canvas_prod.itemconfig(1, width=event.width)
        
        self.canvas_prod.bind("<Configure>", ajustar_ventana_canvas)

    def _construir_panel_derecho(self) -> None:
        # --- Header Total ---
        header: tk.Frame = tk.Frame(self.right_panel, bg=COLORS["primary"], padx=20, pady=20)
        header.pack(fill="x")
        
        tk.Label(header, text="TOTAL VENTA", fg="#BFDBFE", bg=COLORS["primary"], 
                font=("Segoe UI", 10)).pack(anchor="w")
        
        self.lbl_total: tk.Label = tk.Label(header, text="$ 0.00", fg="white", bg=COLORS["primary"], 
                                            font=("Segoe UI", 24, "bold"))
        self.lbl_total.pack(anchor="w")

        # --- Nueva sección: Subtotal y IVA ---
        detalle_frame = tk.Frame(header, bg=COLORS["primary"])
        detalle_frame.pack(anchor="w", pady=(10, 0))
        
        # Subtotal
        self.lbl_subtotal = tk.Label(detalle_frame, text="Subtotal: $ 0.00", 
                                     font=("Segoe UI", 9), bg=COLORS["primary"], 
                                     fg="#BFDBFE", anchor="w")
        self.lbl_subtotal.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        # IVA (16%)
        self.lbl_iva = tk.Label(detalle_frame, text="IVA 16%: $ 0.00", 
                                font=("Segoe UI", 9), bg=COLORS["primary"], 
                                fg="#BFDBFE", anchor="w")
        self.lbl_iva.grid(row=0, column=1, sticky="w")

        # --- Información de Productos en Carrito ---
        tk.Label(self.right_panel, text="🧺 CARRITO DE COMPRAS", font=("Segoe UI", 11, "bold"), 
                bg="white", fg=COLORS["text_dark"]).pack(anchor="w", padx=20, pady=(15, 5))

        # --- Contador de Items ---
        self.lbl_item_count = tk.Label(self.right_panel, text="0 items", font=("Segoe UI", 9), 
                                      bg="white", fg=COLORS["text_gray"])
        self.lbl_item_count.pack(anchor="w", padx=20)

        # --- Lista del Carrito ---
        # Contenedor con scrollbar para carrito
        cart_scroll_frame = tk.Frame(self.right_panel, bg="white")
        cart_scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Canvas para carrito
        self.canvas_cart = tk.Canvas(cart_scroll_frame, bg="white", highlightthickness=0)
        self.cart_container = tk.Frame(self.canvas_cart, bg="white")
        
        # Scrollbar para carrito
        scroll_cart = ttk.Scrollbar(cart_scroll_frame, orient="vertical", command=self.canvas_cart.yview)
        self.canvas_cart.configure(yscrollcommand=scroll_cart.set)
        
        # Crear ventana en canvas
        self.canvas_cart.create_window((0, 0), window=self.cart_container, anchor="nw")
        
        # Configurar scroll del carrito
        def configurar_scroll_cart(e):
            self.canvas_cart.configure(scrollregion=self.canvas_cart.bbox("all"))
        
        self.cart_container.bind("<Configure>", configurar_scroll_cart)
        
        # Posicionar widgets del carrito
        self.canvas_cart.pack(side="left", fill="both", expand=True)
        scroll_cart.pack(side="right", fill="y")

        # --- Configuración de Salida ---
        config_fr: tk.Frame = tk.Frame(self.right_panel, bg="white", padx=20, pady=15)
        config_fr.pack(fill="x", side="bottom", pady=(0, 20))
        
        tk.Label(config_fr, text="Tipo de Operación:", font=("Segoe UI", 9), 
                bg="white", fg=COLORS["text_gray"]).pack(anchor="w")
        
        self.combo_ops: ttk.Combobox = ttk.Combobox(
            config_fr, 
            values=["Venta Directa", "Pedido Web", "Transferencia"], 
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.combo_ops.current(0)
        self.combo_ops.pack(fill="x", pady=(5, 15))

        # --- Botón Acción ---
        tk.Button(config_fr, text="✅ PROCESAR SALIDA", bg=COLORS["primary"], fg="white", 
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=12, cursor="hand2",
                  command=self.procesar_venta).pack(fill="x")

        # Botón vaciar carrito
        tk.Button(config_fr, text="🗑️ Vaciar Carrito", bg=COLORS["border"], fg=COLORS["text_dark"],
                  font=("Segoe UI", 10), relief="flat", pady=8, cursor="hand2",
                  command=self.vaciar_carrito).pack(fill="x", pady=(5, 0))

    def cargar_productos(self, filtro: str = "") -> None:
        # Limpiar lista visual
        for widget in self.frame_list.winfo_children():
            widget.destroy()

        try:
            # Obtener productos de la DB
            # Estructura de get_all_products(): (id, name, sku, category, stock, location, precio, proveedor, estado)
            productos = get_all_products()
            
            # DEBUG: Ver cuántos productos hay
            print(f"📊 Productos encontrados: {len(productos)}")
            
            if not productos:
                tk.Label(self.frame_list, text="No hay productos disponibles", 
                        font=("Segoe UI", 10), fg=COLORS["text_gray"], 
                        bg=COLORS["bg_main"]).pack(pady=50)
                return
                
            for p in productos:
                # Desempaquetar según la estructura actual
                producto_id = p[0]      # id
                nombre = p[1]           # name
                sku = p[2]              # sku/barcode
                categoria = p[3]        # category
                stock = p[4]            # total_stock
                unidad_medida = p[5] 
                ubicacion = p[6]        # location
                precio = p[7]           # precio
                proveedor = p[8]        # proveedor
                estado = p[9]           # estado
                
                # Aplicar filtro
                if filtro and filtro.lower() not in str(nombre).lower() and filtro.lower() not in str(sku).lower():
                    continue
                    
                # Crear fila
                self._crear_fila_producto(
                    producto_id=producto_id,
                    nombre=nombre,
                    sku=sku,
                    stock=stock,
                    unidad=unidad_medida,
                    precio=float(precio) if precio else 0,
                    ubicacion=ubicacion,
                    estado=estado
                )
                
        except Exception as e:
            print(f"❌ Error al cargar productos: {e}")
            tk.Label(self.frame_list, text="Error al cargar productos", 
                    font=("Segoe UI", 10), fg=COLORS["danger"], bg=COLORS["bg_main"]).pack(pady=20)

    def _crear_fila_producto(self, producto_id: int, nombre: str, sku: str, stock: int, 
                           unidad: str, precio: float, ubicacion: str, estado: str) -> None:

        row: tk.Frame = tk.Frame(self.frame_list, bg="white", pady=8)
        row.pack(fill="x", pady=2, padx=5)
        
        # Configurar columnas con grid para mejor control
        for i, weight in enumerate(COLUMN_WEIGHTS):
            row.columnconfigure(i, weight=weight, uniform="table_col")

        # Nombre del producto (truncado)
        f_prod: tk.Frame = tk.Frame(row, bg="white")
        f_prod.grid(row=0, column=0, sticky="w", padx=10)

        nombre_display = nombre
        if len(nombre_display) > 25:
            nombre_display = nombre_display[:22] + "..."
        
        lbl_name: tk.Label = tk.Label(f_prod, text=nombre_display, font=("Segoe UI", 9, "bold"), bg="white", anchor="w", justify="left", width=25)
        lbl_name.grid(row=0, column=0, sticky="we")

        if len(nombre_display) > 22: 
            ToolTip(lbl_name, nombre_display)

        # SKU
        tk.Label(row, text=sku, font=("Segoe UI", 9, "bold"), bg="white", 
                fg=COLORS["text_gray"], anchor="w", justify="left").grid(row=0, column=1, sticky="we", padx=10)
        
        # Stock con color según estado
        if estado == "Out of Stock":
            color_stock = COLORS["error_fg"]
            stock_text = "0"
        elif estado == "Low Stock":
            color_stock = COLORS["warning_fg"]
            stock_text = str(stock)
        else:
            color_stock = COLORS["success_fg"]
            stock_text = str(stock)
            
        tk.Label(row, text=stock_text, font=("Segoe UI", 9, "bold"), 
                bg="white", fg=color_stock, anchor="w", justify="left").grid(row=0, column=2, sticky="we", padx=10)
        
        # Precio
        tk.Label(row, text=f"${precio:.2f}", font=("Segoe UI", 9), 
                bg="white", anchor="w", justify="left").grid(row=0, column=3, sticky="we", padx=10)
        
        # Ubicación
        ubicacion_display = ubicacion or "Sin ubicación"
        if len(ubicacion_display) > 15:
            ubicacion_display = ubicacion_display[:12] + "..."
            
        tk.Label(row, text=ubicacion_display, font=("Segoe UI", 8), 
                bg="#F3F4F6", padx=5, anchor="w", justify="left").grid(row=0, column=4, sticky="we", padx=10)

        # Columna ACCIÓN con dos botones
        action_frame = tk.Frame(row, bg="white")
        action_frame.grid(row=0, column=5, padx=5, sticky="e")
        
        # Botón Agregar (deshabilitado si no hay stock)
        btn_text = "＋" if stock > 0 else "⨯"
        btn_state = "normal" if stock > 0 else "disabled"
        
        btn_add: tk.Button = tk.Button(
            action_frame, 
            text=btn_text, 
            bg=COLORS["primary"] if stock > 0 else COLORS["border"],
            fg="white" if stock > 0 else COLORS["text_gray"],
            font=("Segoe UI", 10, "bold"),
            relief="flat", 
            width=3,
            cursor="hand2" if stock > 0 else "arrow",
            state=btn_state,
            command=lambda pid=producto_id, pname=nombre, psku=sku, pprice=precio: 
                self.agregar_al_carrito(pid, pname, psku, pprice)
        )
        btn_add.pack(side="left", padx=(0, 2))
        
        # Botón Quitar (solo visible si el producto ya está en el carrito)
        btn_remove: tk.Button = tk.Button(
            action_frame, 
            text="−", 
            bg=COLORS["danger"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", 
            width=3,
            cursor="hand2",
            command=lambda pid=producto_id, pprice=precio: 
                self.quitar_del_carrito(pid, pprice)
        )
        btn_remove.pack(side="left")

        # Verificar si el producto está en el carrito para habilitar/quitar botón
        en_carrito = any(item['id'] == producto_id for item in self.cart_items)
        btn_remove.config(state="normal" if en_carrito else "disabled")

        # Separador
        tk.Frame(self.frame_list, bg=COLORS["border"], height=1).pack(fill="x", pady=1)

    def agregar_al_carrito(self, producto_id: int, nombre: str, sku: str, precio: float) -> None:
        # Verificar si el producto ya está en el carrito
        for item in self.cart_items:
            if item['id'] == producto_id:
                # Si ya está, aumentar cantidad
                item['cantidad'] += 1
                item['subtotal'] = item['cantidad'] * precio
                self._renderizar_carrito()
                self._actualizar_botones_accion(producto_id)
                return
        
        # Si no está, agregarlo
        self.cart_items.append({
            'id': producto_id,
            'nombre': nombre,
            'sku': sku,
            'precio': precio,
            'cantidad': 1,
            'subtotal': precio
        })
        
        self._renderizar_carrito()
        self._actualizar_botones_accion(producto_id)

    def quitar_del_carrito(self, producto_id: int, precio: float) -> None:
        # Buscar el producto en el carrito
        for item in self.cart_items:
            if item['id'] == producto_id:
                if item['cantidad'] > 1:
                    # Disminuir cantidad
                    item['cantidad'] -= 1
                    item['subtotal'] = item['cantidad'] * precio
                else:
                    # Eliminar si la cantidad llega a 0
                    self.cart_items = [i for i in self.cart_items if i['id'] != producto_id]
                
                self._renderizar_carrito()
                self._actualizar_botones_accion(producto_id)
                return

    def _actualizar_botones_accion(self, producto_id: int) -> None:
        """Actualiza el estado de los botones de acción en la fila del producto."""
        # Esta función necesitaría acceso a las filas individuales para actualizar los botones
        # En una implementación más compleja, se podría almacenar referencia a los botones
        # Por ahora, recargamos la vista completa (simplificado)
        filtro = self.entry_search.get()
        if filtro == "Buscar por SKU o nombre...":
            filtro = ""
        self.cargar_productos(filtro)

    def _renderizar_carrito(self) -> None:
        # Limpiar contenedor
        for widget in self.cart_container.winfo_children():
            widget.destroy()
        
        if not self.cart_items:
            tk.Label(self.cart_container, text="Carrito vacío", 
                    font=("Segoe UI", 10), fg=COLORS["text_gray"], 
                    bg="white").pack(expand=True, pady=50)
            self.lbl_total.config(text="$ 0.00")
            self.lbl_subtotal.config(text="Subtotal: $ 0.00")
            self.lbl_iva.config(text="IVA 16%: $ 0.00")
            self.lbl_item_count.config(text="0 items")
            return
        
        subtotal: float = 0.0
        
        for idx, item in enumerate(self.cart_items):
            subtotal_item = float(item['precio']) * int(item['cantidad'])
            subtotal += subtotal_item
            
            # Frame del item
            row = tk.Frame(self.cart_container, bg="white", pady=8)
            row.pack(fill="x", pady=2)
            
            # Nombre y SKU
            tk.Label(row, text=f"{item['nombre']}", 
                    font=("Segoe UI", 9, "bold"), bg="white", 
                    anchor="w").pack(anchor="w", padx=5)
            
            # Detalles (SKU, cantidad, precio)
            info = tk.Frame(row, bg="white")
            info.pack(fill="x", padx=5, pady=2)
            
            tk.Label(info, text=f"SKU: {item['sku']}", 
                    font=("Segoe UI", 8), fg=COLORS["text_gray"], 
                    bg="white").pack(side="left")
            
            # Cantidad con controles
            qty_frame = tk.Frame(info, bg="white")
            qty_frame.pack(side="right")
            
            # Botón disminuir
            tk.Button(qty_frame, text="−", font=("Segoe UI", 8), 
                     bg=COLORS["border"], fg=COLORS["text_dark"],
                     relief="flat", width=2, cursor="hand2",
                     command=lambda i=idx: self.ajustar_cantidad(i, -1)).pack(side="left")
            
            # Cantidad
            tk.Label(qty_frame, text=f" {item['cantidad']} ", 
                    font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
            
            # Botón aumentar
            tk.Button(qty_frame, text="＋", font=("Segoe UI", 8), 
                     bg=COLORS["primary"], fg="white",
                     relief="flat", width=2, cursor="hand2",
                     command=lambda i=idx: self.ajustar_cantidad(i, 1)).pack(side="left")
            
            # Precio y subtotal
            price_frame = tk.Frame(row, bg="white")
            price_frame.pack(fill="x", padx=5)
            
            tk.Label(price_frame, text=f"${item['precio']:.2f} c/u", 
                    font=("Segoe UI", 8), fg=COLORS["text_gray"], 
                    bg="white").pack(side="left")
            
            tk.Label(price_frame, text=f"${subtotal_item:.2f}", 
                    font=("Segoe UI", 9, "bold"), bg="white").pack(side="right")
            
            # Botón eliminar
            tk.Button(row, text="✕ Eliminar", font=("Segoe UI", 8), 
                     bg=COLORS["error_bg"], fg=COLORS["error_fg"],
                     relief="flat", cursor="hand2",
                     command=lambda i=idx: self.eliminar_del_carrito(i)).pack(anchor="e", padx=5, pady=2)
            
            # Separador
            tk.Frame(self.cart_container, bg=COLORS["border"], height=1).pack(fill="x", pady=2)
        
        # Calcular totales
        iva = subtotal * 0.16
        total = subtotal + iva
        
        # Actualizar totales en la UI
        self.lbl_total.config(text=f"$ {total:,.2f}")
        self.lbl_subtotal.config(text=f"Subtotal: $ {subtotal:,.2f}")
        self.lbl_iva.config(text=f"IVA 16%: $ {iva:,.2f}")
        self.lbl_item_count.config(text=f"{len(self.cart_items)} items")
        
        # Asegurar que el canvas se actualice
        self.cart_container.update_idletasks()
        self.canvas_cart.configure(scrollregion=self.canvas_cart.bbox("all"))

    def ajustar_cantidad(self, idx: int, cambio: int) -> None:
        if 0 <= idx < len(self.cart_items):
            nueva_cantidad = self.cart_items[idx]['cantidad'] + cambio
            
            if nueva_cantidad <= 0:
                # Eliminar si la cantidad llega a 0
                self.cart_items.pop(idx)
                self._actualizar_botones_accion(self.cart_items[idx]['id'] if idx < len(self.cart_items) else None)
            else:
                self.cart_items[idx]['cantidad'] = nueva_cantidad
                self.cart_items[idx]['subtotal'] = nueva_cantidad * self.cart_items[idx]['precio']
            
            self._renderizar_carrito()

    def eliminar_del_carrito(self, idx: int) -> None:
        if 0 <= idx < len(self.cart_items):
            producto_id = self.cart_items[idx]['id']
            self.cart_items.pop(idx)
            self._renderizar_carrito()
            self._actualizar_botones_accion(producto_id)

    def vaciar_carrito(self) -> None:
        # Obtener IDs de productos para actualizar botones
        productos_ids = [item['id'] for item in self.cart_items]
        
        self.cart_items.clear()
        self._renderizar_carrito()
        
        # Actualizar botones de acción para todos los productos afectados
        for producto_id in productos_ids:
            self._actualizar_botones_accion(producto_id)

    def procesar_venta(self) -> None:
        if not self.cart_items:
            messagebox.showwarning("Carrito Vacío", "Agrega productos al carrito antes de procesar.")
            return
        
        tipo_operacion: str = self.combo_ops.get()
        
        # Preparar lista de productos
        productos_venta: list[dict[str, Any]] = [
            {
                'id': item['id'],
                'nombre': item['nombre'],
                'precio': item['precio'],
                'cantidad': item['cantidad']
            } for item in self.cart_items
        ]

        try:
            # 1. Intentar crear la orden
            orden_id: Optional[int] = crear_orden_venta(
                tipo_operacion=tipo_operacion,
                cliente_id=None,
                usuario_id=self.user_id,
                productos=productos_venta
            )
            
            if not orden_id:
                messagebox.showerror("❌ Error", "No se pudo crear la orden. Posible duplicado o error de stock.")
                return

            # 2. Procesar inventario y recolectar alertas
            errores_stock: list[str] = []
            for item in self.cart_items:
                try:
                    self.inv_manager.registrar_salida(
                        product_id=item['id'],
                        quantity=item['cantidad'],
                        razon="venta",
                        razon_detalle=f"Orden #{orden_id} ({tipo_operacion})",
                        user_id=self.user_id
                    )
                except ValueError as ve:
                    errores_stock.append(f"• {item['nombre']}: {str(ve)}")
                except Exception:
                    errores_stock.append(f"• {item['nombre']}: Error inesperado en stock")

            # 3. Calcular totales para el resumen
            subtotal: float = sum(item['precio'] * item['cantidad'] for item in self.cart_items)
            iva: float = subtotal * 0.16
            total: float = subtotal + iva
            
            # 4. Construir mensaje UNIFICADO
            resumen_msg: str = (
                f"✅ Venta Procesada Correctamente\n"
                f"{'='*35}\n"
                f"Orden: #{orden_id}\n"
                f"Operación: {tipo_operacion}\n\n"
                f"Subtotal: ${subtotal:,.2f}\n"
                f"IVA (16%): ${iva:,.2f}\n"
                f"TOTAL: ${total:,.2f}\n"
                f"{'='*35}\n"
                f"Productos procesados: {len(self.cart_items)}"
            )

            # Añadir alertas si existen
            if errores_stock:
                resumen_msg += "\n\n⚠️ ALERTAS DE INVENTARIO:\n" + "\n".join(errores_stock)
                messagebox.showwarning("Procesado con Observaciones", resumen_msg)
            else:
                messagebox.showinfo("Éxito", resumen_msg)

            # 5. Finalizar proceso
            self.vaciar_carrito()
            
        except Exception as e:
            messagebox.showerror("❌ Error del Sistema", f"Error crítico al procesar:\n{str(e)}")

    # Métodos para búsqueda
    def _on_search_focus_in(self, event=None) -> None:
        if self.entry_search.get() == "Buscar por SKU o nombre...":
            self.entry_search.delete(0, tk.END)
            self.entry_search.config(fg=COLORS["text_dark"])

    def _on_search_focus_out(self, event=None) -> None:
        if not self.entry_search.get():
            self.entry_search.insert(0, "Buscar por SKU o nombre...")
            self.entry_search.config(fg=COLORS["text_gray"])

    def _on_search_key_release(self, event=None) -> None:
        filtro = self.entry_search.get()
        if filtro != "Buscar por SKU o nombre...":
            self.cargar_productos(filtro)