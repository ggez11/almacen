import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime

# Importaciones locales
from database.queries import get_movimientos_history, obtener_movimientos_por_fecha, obtener_ubicaciones
from services.auth_service import get_current_user

# Componentes
from gui.components.tooltip import ToolTip

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
    "success_bg": "#D1FAE5", "success_fg": "#065F46",  # Para IN
    "warning_bg": "#FEF3C7", "warning_fg": "#92400E",  # Para OUT
    "blue_dot": "#3B82F6",
    "green_text": "#10B981",  # Entrada
    "red_text": "#EF4444",    # Salida
    "error_bg": "#FEE2E2", "error_fg": "#991B1B"
}

COLUMN_WEIGHTS: List[int] = [4, 10, 5, 5, 5, 5, 5, 6]

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
        self.scrollbar_vertical: Optional[ttk.Scrollbar] = None
        self.scrollbar_horizontal: Optional[ttk.Scrollbar] = None

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
        
        tk.Label(title_row, text="📊 Historial de Movimientos", 
                 font=FONT_TITLE, bg=COLORS["bg_main"], fg=COLORS["text_header"]).pack(side="left")
        
        # Botón Actualizar
        tk.Button(title_row, text="🔄 Actualizar", bg=COLORS["white"], fg=COLORS["text_body"],
                  relief="solid", bd=0, highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=15, pady=6, cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=self.cargar_datos_historial).pack(side="right", padx=5)

    def _construir_filtros(self) -> None:
        filter_bar: tk.Frame = tk.Frame(self.main_content, bg=COLORS["white"], padx=15, pady=15)
        filter_bar.pack(fill="x", pady=(0, 20))

        # Filtro por fecha
        tk.Label(filter_bar, text="Fecha desde:", font=FONT_SMALL, 
                bg=COLORS["white"], fg=COLORS["text_light"]).pack(side="left", padx=5)
        
        self.entry_fecha_desde = tk.Entry(filter_bar, width=12, font=FONT_SMALL,
                                         bg="#F3F4F6", relief="solid", borderwidth=1)
        self.entry_fecha_desde.pack(side="left", padx=5)
        
        tk.Label(filter_bar, text="hasta:", font=FONT_SMALL, 
                bg=COLORS["white"], fg=COLORS["text_light"]).pack(side="left", padx=5)
        
        self.entry_fecha_hasta = tk.Entry(filter_bar, width=12, font=FONT_SMALL,
                                         bg="#F3F4F6", relief="solid", borderwidth=1)
        self.entry_fecha_hasta.pack(side="left", padx=5)
        
        # Botón aplicar filtro fecha
        tk.Button(filter_bar, text="Filtrar por fecha", bg=COLORS["primary"], fg="white",
                 font=FONT_SMALL, relief="flat", padx=10, pady=5, cursor="hand2",
                 command=self.aplicar_filtro_fecha).pack(side="left", padx=10)

        # Filtro por tipo
        tk.Label(filter_bar, text="Tipo:", font=FONT_SMALL, 
                bg=COLORS["white"], fg=COLORS["text_light"]).pack(side="left", padx=(20, 5))
        
        self.combo_tipo = ttk.Combobox(filter_bar, values=["Todos", "IN", "OUT"], 
                                      state="readonly", font=FONT_SMALL, width=10)
        self.combo_tipo.set("Todos")
        self.combo_tipo.pack(side="left", padx=5)
        self.combo_tipo.bind("<<ComboboxSelected>>", self.aplicar_filtro_tipo)

        # Filtro por ubicación
        tk.Label(filter_bar, text="Ubicación:", font=FONT_SMALL, 
                bg=COLORS["white"], fg=COLORS["text_light"]).pack(side="left", padx=(20, 5))
        
        ubicaciones = obtener_ubicaciones()
        ubicacion_options = ["Todas"] + [ub[1] for ub in ubicaciones]
        self.combo_ubicacion = ttk.Combobox(filter_bar, values=ubicacion_options,
                                           state="readonly", font=FONT_SMALL, width=12)
        self.combo_ubicacion.set("Todas")
        self.combo_ubicacion.pack(side="left", padx=5)
        self.combo_ubicacion.bind("<<ComboboxSelected>>", self.aplicar_filtro_ubicacion)

        # Búsqueda
        search_container: tk.Frame = tk.Frame(filter_bar, bg="#F3F4F6", padx=10, pady=5)
        search_container.pack(side="right", fill="y")
        
        tk.Label(search_container, text="🔍", bg="#F3F4F6", fg=COLORS["text_light"]).pack(side="left")
        
        self.search_entry = tk.Entry(
            search_container,
            bg="#F3F4F6",
            bd=0,
            width=30,
            font=FONT_BODY,
            fg=COLORS["text_body"]
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.insert(0, "Buscar producto, razón...")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)

        # Botón limpiar
        tk.Button(filter_bar, text="Limpiar Filtros", fg=COLORS["primary"], bg=COLORS["white"], 
                 bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", 
                 command=self.limpiar_filtros).pack(side="right", padx=15)

    def _construir_tabla_movimientos(self) -> None:
        table_container: tk.Frame = tk.Frame(self.main_content, bg=COLORS["white"],
                                             highlightbackground=COLORS["border"], highlightthickness=1)
        table_container.pack(fill="both", expand=True)

        # Header de Columnas (CAMBIO: USUARIO → PROVEEDOR)
        headers: List[str] = ["FECHA Y HORA", "PRODUCTO", "TIPO", "CANTIDAD", "RAZÓN", "PROVEEDOR", "UBICACIÓN", "DETALLES"]
        
        header_fr: tk.Frame = tk.Frame(table_container, bg="#F9FAFB", height=45)
        header_fr.pack(fill="x")

        for i, (h_text, w) in enumerate(zip(headers, COLUMN_WEIGHTS)):
            header_fr.columnconfigure(i, weight=w, uniform="table_col")
            tk.Label(header_fr, text=h_text, bg="#F9FAFB", fg=COLORS["text_light"],
                     font=FONT_HEAD, anchor="w").grid(row=0, column=i, sticky="we", padx=8, pady=12)

        # Contenedor principal para canvas y scrollbars
        canvas_container = tk.Frame(table_container, bg=COLORS["white"])
        canvas_container.pack(fill="both", expand=True)
        
        # Crear canvas
        self.canvas = tk.Canvas(canvas_container, bg=COLORS["white"], highlightthickness=0)
        
        # Scrollbar vertical
        self.scrollbar_vertical = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        
        # Scrollbar horizontal (NUEVO)
        self.scrollbar_horizontal = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        # Frame scrollable dentro del canvas
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS["white"])

        # Configurar el canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Crear ventana en el canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configurar el tamaño del canvas window para que se ajuste al contenido
        self.canvas.bind("<Configure>", self._ajustar_ventana_canvas)
        
        # Configurar scrollbars
        self.canvas.configure(
            yscrollcommand=self.scrollbar_vertical.set,
            xscrollcommand=self.scrollbar_horizontal.set  # NUEVO: scroll horizontal
        )
        
        # Usar grid para mejor control
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_vertical.grid(row=0, column=1, sticky="ns")
        self.scrollbar_horizontal.grid(row=1, column=0, sticky="ew")
        
        # Configurar expansión
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)

        # Cargar datos iniciales
        self.cargar_datos_historial()

    def _ajustar_ventana_canvas(self, event):
        """Ajusta el ancho de la ventana del canvas al ancho del canvas."""
        if self.canvas and self.canvas_window:
            self.canvas.itemconfig(self.canvas_window, width=event.width)

    def cargar_datos_historial(self, filtro_fecha: bool = False) -> None:
        """Consulta la DB y refresca la lista de movimientos."""
        if not self.scrollable_frame: 
            return

        # Limpiar tabla
        for w in self.scrollable_frame.winfo_children(): 
            w.destroy()

        try:
            # Obtener datos de la base de datos
            if filtro_fecha and self.entry_fecha_desde.get() and self.entry_fecha_hasta.get():
                movimientos_data = obtener_movimientos_por_fecha(
                    self.entry_fecha_desde.get(), 
                    self.entry_fecha_hasta.get()
                )
            else:
                movimientos_data = get_movimientos_history()

            if not movimientos_data:
                tk.Label(self.scrollable_frame, text="No hay movimientos registrados", 
                        font=FONT_BODY, fg=COLORS["text_light"], bg=COLORS["white"]).pack(pady=50)
                return

            # Procesar cada movimiento
            for mov in movimientos_data:
                # Verificar que el movimiento tenga suficientes elementos
                if len(mov) < 7:  # Necesitamos al menos 7 elementos
                    print(f"⚠ Movimiento incompleto: {mov}")
                    continue
                    
                # Estructura esperada de get_movimientos_history():
                # (fecha_movimiento, producto, tipo, cantidad, razon, usuario, ubicacion, observaciones)
                fecha_movimiento = str(mov[0])
                producto = str(mov[1]) if len(mov) > 1 else ""
                tipo = str(mov[2]) if len(mov) > 2 else "IN"
                cantidad = int(mov[3]) if len(mov) > 3 and mov[3] is not None else 0
                razon = str(mov[4]) if len(mov) > 4 else ""
                # CAMBIO: Usuario → Proveedor (campo 5 ahora es proveedor)
                proveedor = str(mov[5]) if len(mov) > 5 else ""
                ubicacion = str(mov[6]) if len(mov) > 6 else ""
                observaciones = str(mov[7]) if len(mov) > 7 else ""
                
                # Extraer SKU si está disponible (algunas consultas pueden tenerlo)
                sku = str(mov[8]) if len(mov) > 8 else ""
                
                # Aplicar filtros (CAMBIO: usuario → proveedor)
                if self._aplicar_filtros(fecha_movimiento, producto, tipo, razon, proveedor, ubicacion):
                    self._crear_fila(
                        fecha_movimiento=fecha_movimiento,
                        producto=producto,
                        sku=sku,
                        tipo=tipo,
                        cantidad=cantidad,
                        razon=razon,
                        proveedor=proveedor,
                        ubicacion=ubicacion,
                        observaciones=observaciones
                    )

        except Exception as e:
            print(f"❌ Error al cargar movimientos: {e}")
            import traceback
            traceback.print_exc()
            tk.Label(self.scrollable_frame, text="Error al cargar movimientos", 
                    font=FONT_BODY, fg=COLORS["error_fg"], bg=COLORS["white"]).pack(pady=50)

    def _aplicar_filtros(self, fecha: str, producto: str, tipo: str, 
                        razon: str, proveedor: str, ubicacion: str) -> bool:
        """Aplica todos los filtros activos de manera robusta."""
        
        # 1. Filtro de búsqueda (Texto libre)
        search_text: str = self.search_entry.get().lower().strip()
        if search_text and search_text != "buscar producto, razón...":
            # Creamos una cadena con todo el contenido para buscar fácilmente
            row_content: str = f"{producto} {razon} {proveedor} {fecha}".lower()
            if search_text not in row_content:
                return False

        # 2. Filtro por TIPO (CORREGIDO)
        tipo_filtro: str = self.combo_tipo.get() # Valores: "Todos", "IN", "OUT"
        
        if tipo_filtro != "Todos":
            # Normalizamos el valor que viene de la Base de Datos
            tipo_db_str: str = str(tipo).upper().strip()
            
            # Determinamos si el registro en DB es realmente una ENTRADA
            # Usamos la misma lógica que usaste en _crear_fila para ser consistentes
            es_entrada_db: bool = "IN" in tipo_db_str
            
            # Lógica de filtrado
            if tipo_filtro == "IN" and not es_entrada_db:
                return False # El usuario quiere IN, pero esto es OUT
            
            if tipo_filtro == "OUT" and es_entrada_db:
                return False # El usuario quiere OUT, pero esto es IN

        # 3. Filtro por UBICACIÓN
        ubicacion_filtro: str = self.combo_ubicacion.get()
        if ubicacion_filtro != "Todas":
            # Normalizamos también la ubicación por seguridad
            if str(ubicacion_filtro).strip() != str(ubicacion).strip():
                return False

        return True

    def _crear_fila(self, fecha_movimiento: str, producto: str, sku: str, tipo: str, 
                   cantidad: int, razon: str, proveedor: str, ubicacion: str, observaciones: str) -> None:  # CAMBIO: usuario → proveedor
        if not self.scrollable_frame: 
            return

        row: tk.Frame = tk.Frame(self.scrollable_frame, bg=COLORS["white"], pady=10)
        row.pack(fill="x")

        for i, w in enumerate(COLUMN_WEIGHTS): 
            row.columnconfigure(i, weight=w, uniform="table_col")
        
        # 1. Fecha y Hora
        fecha_formateada = fecha_movimiento[:19] if len(fecha_movimiento) > 19 else fecha_movimiento
        lbl_fecha = tk.Label(row, text=fecha_formateada, font=FONT_SMALL, bg=COLORS["white"], 
                           fg=COLORS["text_body"], anchor="w")
        lbl_fecha.grid(row=0, column=0, sticky="w", padx=5)

        # 2. Producto (con SKU si está disponible)
        f_prod: tk.Frame = tk.Frame(row, bg=COLORS['white'])
        f_prod.grid(row=0, column=1, sticky="nsew", padx=5)

        f_prod.columnconfigure(1, weight=1)        

        producto_text = producto
        if sku:
            producto_text = f"{producto}\nSKU: {sku}"
        
        if len(producto_text) > 25:
            producto_text = producto_text[:22] + "..."        

        tk.Label(f_prod, text="📦", font=("Arial", 12), bg="#EEE", width=3).grid(row=0, column=0, padx=(0, 10))

        lbl_producto = tk.Label(f_prod, text=producto_text, font=("Segoe UI", 9, "bold"), 
                              bg=COLORS["white"], fg=COLORS["text_header"], justify="center",
                              anchor="w", width=25)
        lbl_producto.grid(row=0, column=1, sticky="we")

        if len(producto_text) > 22:
            ToolTip(lbl_producto, producto_text)

        # 3. Tipo Badge (IN/OUT)
        es_entrada: bool = tipo.upper() == "IN" or "↑ IN" in tipo
        bg_color: str = COLORS["success_bg"] if es_entrada else COLORS["warning_bg"]
        fg_color: str = COLORS["success_fg"] if es_entrada else COLORS["warning_fg"]
        tipo_text: str = "↑ IN" if es_entrada else "↓ OUT"
        
        badge_frame = tk.Frame(row, bg=bg_color, padx=8, pady=3)
        badge_frame.grid(row=0, column=2, sticky="we", padx=8)
        tk.Label(badge_frame, text=tipo_text, font=FONT_HEAD, bg=bg_color, fg=fg_color, anchor="w", justify="left",).grid(row=0, column=2, sticky="we", padx=8)

        # 4. Cantidad
        cantidad_text = f"+{cantidad}" if es_entrada else f"-{cantidad}"
        cantidad_color = COLORS["green_text"] if es_entrada else COLORS["red_text"]
        lbl_cantidad = tk.Label(row, text=cantidad_text, font=("Segoe UI", 9, "bold"), 
                              bg=COLORS["white"], fg=cantidad_color, anchor="center", justify="left",)
        lbl_cantidad.grid(row=0, column=3, sticky="we", padx=5)

        # 5. Razón
        razon_display = razon
        if len(razon_display) > 20:
            razon_display = razon_display[:17] + "..."
        lbl_razon = tk.Label(row, text=razon_display, font=FONT_BODY, bg=COLORS["white"], 
                           fg=COLORS["text_body"], anchor="center", justify="left")
        lbl_razon.grid(row=0, column=4, sticky="we", padx=5)

        # 6. PROVEEDOR (CAMBIO: Usuario → Proveedor)
        lbl_proveedor = tk.Label(row, text=f"🏢 {proveedor}", font=FONT_SMALL, bg=COLORS["white"], 
                               fg=COLORS["text_light"], anchor="center", justify="left")
        lbl_proveedor.grid(row=0, column=5, sticky="we", padx=5)

        # 7. Ubicación
        ubicacion_display = ubicacion or "N/A"
        lbl_ubicacion = tk.Label(row, text=f"📍 {ubicacion_display}", font=FONT_SMALL, 
                               bg=COLORS["white"], fg=COLORS["text_light"], anchor="center", justify="left")
        lbl_ubicacion.grid(row=0, column=6, sticky="we", padx=5)

        # 8. Botón Detalles (ACTUALIZADO: siempre visible, muestra todos los detalles)
        btn_detalles = tk.Button(row, text="📋 Detalles", font=("Segoe UI", 8), 
                                bg=COLORS["primary"], fg="white",
                                relief="flat", cursor="hand2",
                                command=lambda: self.mostrar_detalles_completos(
                                    fecha_movimiento, producto, sku, tipo, 
                                    cantidad, razon, proveedor, ubicacion, observaciones
                                ))
        btn_detalles.grid(row=0, column=7, sticky="we", padx=5)

        # Línea divisoria
        tk.Frame(self.scrollable_frame, bg=COLORS["border"], height=1).pack(fill="x")

    def mostrar_detalles_completos(self, fecha: str, producto: str, sku: str, tipo: str, 
                                 cantidad: int, razon: str, proveedor: str, ubicacion: str, 
                                 observaciones: str) -> None:
        """Muestra todos los detalles del movimiento en un modal."""
        modal = tk.Toplevel(self)
        modal.title("📋 Detalles Completos del Movimiento")
        modal.geometry("500x650")
        modal.configure(bg="white")
        modal.resizable(False, False)
        
        # Centrar ventana
        modal.update_idletasks()
        width = modal.winfo_width()
        height = modal.winfo_height()
        x = (modal.winfo_screenwidth() // 2) - (width // 2)
        y = (modal.winfo_screenheight() // 2) - (height // 2)
        modal.geometry(f'{width}x{height}+{x}+{y}')
        
        # Encabezado
        header = tk.Frame(modal, bg=COLORS["primary"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="📋 DETALLES DEL MOVIMIENTO", 
                font=("Segoe UI", 14, "bold"), bg=COLORS["primary"], 
                fg="white").pack(expand=True, pady=(20, 5))
        
        tk.Label(header, text="Información completa de la operación", 
                font=("Segoe UI", 9), bg=COLORS["primary"], 
                fg="#E0F2FE").pack(pady=(0, 5))
        
        # Contenido con scroll
        content_frame = tk.Frame(modal, bg="white")
        content_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Canvas con scrollbar
        canvas = tk.Canvas(content_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_content = tk.Frame(canvas, bg="white")
        
        scrollable_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        print(tipo)
        # Widgets
        detalles = [
            ("📅 Fecha y Hora:", fecha[:19] if len(fecha) > 19 else fecha),
            ("📦 Producto:", producto),
            ("🔢 SKU:", sku if sku else "No especificado"),
            ("📊 Tipo:", f"↑ ENTRADA (IN)" if tipo.upper() == "↑ IN" else "↓ SALIDA (OUT)"),
            ("🔢 Cantidad:", f"{'+' if tipo.upper() == '↑ IN' else '-'}{cantidad} unidades"),
            ("📝 Razón:", razon),
            ("🏢 Proveedor:", proveedor if proveedor else "No especificado"),
            ("📍 Ubicación:", ubicacion if ubicacion else "No especificada"),
        ]
        
        for i, (label, valor) in enumerate(detalles):
            frame = tk.Frame(scrollable_content, bg="white")
            frame.pack(fill="x", pady=8)
            
            tk.Label(frame, text=label, font=("Segoe UI", 10, "bold"), 
                    bg="white", fg=COLORS["text_header"], width=15, anchor="w").pack(side="left")
            
            tk.Label(frame, text=valor, font=("Segoe UI", 10), 
                    bg="white", fg=COLORS["text_body"], wraplength=300, justify="left").pack(side="left", padx=(10, 0))
        
        # Observaciones (si existen)
        if observaciones and observaciones.strip():
            tk.Frame(scrollable_content, bg=COLORS["border"], height=1).pack(fill="x", pady=15)
            
            obs_frame = tk.Frame(scrollable_content, bg="white")
            obs_frame.pack(fill="x", pady=5)
            
            tk.Label(obs_frame, text="📝 Observaciones:", font=("Segoe UI", 10, "bold"), 
                    bg="white", fg=COLORS["text_header"], anchor="w").pack(anchor="w")
            
            # Texto con scroll para observaciones largas
            text_frame = tk.Frame(obs_frame, bg="#F9FAFB", relief="solid", borderwidth=1)
            text_frame.pack(fill="x", pady=5)
            
            text_widget = tk.Text(text_frame, wrap="word", height=6, font=("Segoe UI", 9),
                                 bg="#F9FAFB", fg=COLORS["text_body"], relief="flat")
            scrollbar_text = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar_text.set)
            
            text_widget.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            scrollbar_text.pack(side="right", fill="y")
            
            text_widget.insert("1.0", observaciones)
            text_widget.config(state="disabled")
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botón cerrar
        btn_frame = tk.Frame(modal, bg="white", height=70)
        btn_frame.pack(fill="x", side="bottom", pady=(0, 20))
        btn_frame.pack_propagate(False)
        
        tk.Button(btn_frame, text="Cerrar", bg=COLORS["primary"], fg="white",
                 font=("Segoe UI", 10, "bold"), relief="flat", padx=40, pady=10,
                 cursor="hand2", command=modal.destroy).pack(expand=True)

    def aplicar_filtro_fecha(self) -> None:
        """Aplica filtro por fecha."""
        fecha_desde = self.entry_fecha_desde.get()
        fecha_hasta = self.entry_fecha_hasta.get()
        
        if not fecha_desde or not fecha_hasta:
            messagebox.showwarning("Filtro incompleto", "Ingresa ambas fechas (desde y hasta)")
            return
        
        try:
            # Validar formato de fecha (YYYY-MM-DD)
            datetime.strptime(fecha_desde, "%Y-%m-%d")
            datetime.strptime(fecha_hasta, "%Y-%m-%d")
            
            if fecha_desde > fecha_hasta:
                messagebox.showwarning("Fechas inválidas", "La fecha 'desde' debe ser menor que 'hasta'")
                return
                
            self.cargar_datos_historial(filtro_fecha=True)
            
        except ValueError:
            messagebox.showwarning("Formato incorrecto", "Usa el formato YYYY-MM-DD (ej: 2024-01-18)")

    def aplicar_filtro_tipo(self, event=None) -> None:
        """Aplica filtro por tipo."""
        self.cargar_datos_historial()

    def aplicar_filtro_ubicacion(self, event=None) -> None:
        """Aplica filtro por ubicación."""
        self.cargar_datos_historial()

    def limpiar_filtros(self) -> None:
        """Limpia todos los filtros."""
        self.entry_fecha_desde.delete(0, tk.END)
        self.entry_fecha_hasta.delete(0, tk.END)
        self.combo_tipo.set("Todos")
        self.combo_ubicacion.set("Todas")
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "Buscar producto, razón...")
        self.search_entry.config(fg=COLORS["text_light"])
        self.cargar_datos_historial()

    # Métodos para búsqueda
    def _on_search_focus_in(self, event=None) -> None:
        if self.search_entry.get() == "Buscar producto, razón...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=COLORS["text_header"])

    def _on_search_focus_out(self, event=None) -> None:
        if not self.search_entry.get():
            self.search_entry.insert(0, "Buscar producto, razón...")
            self.search_entry.config(fg=COLORS["text_light"])

    def _on_search_key_release(self, event=None) -> None:
        filtro = self.search_entry.get()
        if filtro != "Buscar producto, razón...":
            self.cargar_datos_historial()