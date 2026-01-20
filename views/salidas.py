import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Union

# Importaciones del sistema
from database.queries import get_all_products
from gui.components.widgets import EntryWithPlaceholder

# Services
from services.inv_manager import InventoryManager

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

        self.inv_manager = InventoryManager()

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
            # get_all_products() suele retornar [(id, nombre, sku, categoria, stock, ubicacion), ...]
            productos: List[tuple] = get_all_products()
        except Exception as e:
            print(f"Error al obtener productos: {e}")
            productos = []

        row_frame: Union[tk.Frame, None] = None
        
        for i, p in enumerate(productos):
            if i % 3 == 0:
                row_frame = tk.Frame(self.frame_grid, bg=COLORS["bg_main"])
                row_frame.pack(fill="x", pady=10)
            
            if row_frame:
                # PASO CLAVE: p[0] es el ID, p[1] nombre, p[2] sku, p[4] stock
                self._crear_tarjeta_producto(row_frame, p[0], p[1], p[2], p[4])

    def _crear_tarjeta_producto(self, parent: tk.Frame, p_id: int, name: str, sku: str, stock: int) -> None:
        card: tk.Frame = tk.Frame(parent, bg="white", padx=10, pady=10, width=180, height=150,
                                  highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(side="left", padx=10)
        card.pack_propagate(False)

        tk.Label(card, text=f"{stock} Units", bg="#DCFCE7", fg="#166534", font=("Segoe UI", 8)).pack(anchor="e")
        tk.Label(card, text=name, font=("Segoe UI", 9, "bold"), bg="white", wraplength=160).pack(anchor="w", pady=5)
        
        # El comando lambda ahora incluye p_id
        tk.Button(card, text="+ Agregar", bg=COLORS["bg_main"], fg=COLORS["primary"], relief="flat",
                  command=lambda id_p=p_id, n=name, s=sku: self.agregar_al_manifiesto(id_p, n, s)
                 ).pack(side="bottom", fill="x")

    def agregar_al_manifiesto(self, p_id: int, name: str, sku: str) -> None:
        
        # Evitar duplicados en el manifiesto
        if any(item['id'] == p_id for item in self.manifest_items):
            messagebox.showinfo("Aviso", "Este producto ya está en el manifiesto.")
            return

        self.manifest_items.append({
            "id": p_id, 
            "name": name, 
            "sku": sku
        })
        self._renderizar_manifiesto()

    def _renderizar_manifiesto(self) -> None:
        for w in self.items_container.winfo_children():
            w.destroy()
        
        self.lbl_total_count.config(text=str(len(self.manifest_items)))

        for item in self.manifest_items:
            fr: tk.Frame = tk.Frame(self.items_container, bg="white", pady=5, 
                                    highlightbackground=COLORS["border"], highlightthickness=1)
            fr.pack(fill="x", pady=2)
            
            tk.Label(fr, text=item['name'], font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w", padx=5)
            
            opts: tk.Frame = tk.Frame(fr, bg="white")
            opts.pack(fill="x", padx=5)
            
            # Guardamos el Combobox y el Entry de cantidad en el diccionario del item
            combo: ttk.Combobox = ttk.Combobox(opts, values=["Dañado", "Vencido", "Robo", "Uso Interno"], width=12, state="readonly")
            combo.set("Dañado")
            combo.pack(side="left")
            item['combo_widget'] = combo # <--- Referencia crítica

            qty_entry: tk.Entry = tk.Entry(opts, width=5, highlightthickness=1)
            qty_entry.insert(0, "1")
            qty_entry.pack(side="left", padx=5)
            item['qty_widget'] = qty_entry # <--- Referencia crítica
            
            tk.Button(opts, text="X", bg="white", fg="red", bd=0, width=2,
                      command=lambda i=item: self.eliminar_del_manifiesto(i)).pack(side="right")

    def registrar_ajuste(self) -> None:
        if not self.manifest_items:
            messagebox.showwarning("⚠️ Vacío", "No hay productos en el manifiesto para retirar.")
            return

        confirmar = messagebox.askyesno("Confirmar", f"¿Desea registrar la salida de {len(self.manifest_items)} productos?")
        if not confirmar:
            return

        exitos: int = 0
        errores: list[str] = []

        for item in self.manifest_items:
            try:
                # Extraer datos de los widgets guardados en el renderizado
                p_id: int = item['id']
                cantidad_str: str = item['qty_widget'].get().strip()
                razon: str = item['combo_widget'].get().lower()
                
                if not cantidad_str.isdigit() or int(cantidad_str) <= 0:
                    errores.append(f"{item['name']}: Cantidad inválida")
                    continue
                
                cantidad: int = int(cantidad_str)

                # Llamada al manager de base de datos
                # Nota: Asegúrate que 'inv_manager' esté importado o sea accesible
                resultado: bool = self.inv_manager.registrar_merma(
                    product_id=p_id,
                    cantidad=cantidad,
                    tipo_merma=razon,
                    detalle="Ajuste masivo desde Salidas",
                    user_id=getattr(self, 'user_id', 1) # ID por defecto si no existe
                )

                if resultado:
                    exitos += 1
                else:
                    errores.append(f"{item['name']}: Error en base de datos")

            except Exception as e:
                errores.append(f"{item['name']}: {str(e)}")

        # Resumen final
        mensaje: str = f"✅ Procesados: {exitos} productos."
        if errores:
            mensaje += "\n\n❌ Errores:\n" + "\n".join(errores)
            messagebox.showwarning("Resultado parcial", mensaje)
        else:
            messagebox.showinfo("✅ Éxito Total", mensaje)

        # Limpiar y refrescar
        if exitos > 0:
            self.manifest_items.clear()
            self._renderizar_manifiesto()
            self.cargar_productos_grid() # Actualiza los stocks en las tarjetas