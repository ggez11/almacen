import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Tuple, Optional

# Importaciones de tus módulos
from database.queries import get_all_products, get_movements_history
from services.inv_manager import registrar_entrada, registrar_salida
from services.auth_service import get_current_user

class MovimientosView(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        
        # Atributos tipados
        # self.map_products relaciona el String del Combo con el ID entero del producto
        self.map_products: Dict[str, int] = {} 
        
        # --- Panel Izquierdo: Formulario de Movimiento ---
        left_panel: tk.Frame = tk.Frame(self, padx=10, pady=10, bd=2, relief="groove")
        left_panel.pack(side="left", fill="y")
        
        tk.Label(left_panel, text="REGISTRAR MOVIMIENTO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Widgets como atributos de clase para acceso global en la instancia
        tk.Label(left_panel, text="Producto:").pack(anchor="w")
        self.combo_prods: ttk.Combobox = ttk.Combobox(left_panel, width=30)
        self.combo_prods.pack(pady=5)
        self.cargar_productos_combo()

        tk.Label(left_panel, text="Tipo:").pack(anchor="w")
        self.combo_tipo: ttk.Combobox = ttk.Combobox(left_panel, values=["ENTRADA", "SALIDA"], state="readonly")
        self.combo_tipo.current(0)
        self.combo_tipo.pack(pady=5)

        tk.Label(left_panel, text="Concepto:").pack(anchor="w")
        self.combo_concepto: ttk.Combobox = ttk.Combobox(left_panel, values=["Compra", "Venta", "Merma", "Devolucion", "Ajuste"])
        self.combo_concepto.pack(pady=5)
        
        tk.Label(left_panel, text="Estado Stock:").pack(anchor="w")
        self.combo_estado: ttk.Combobox = ttk.Combobox(left_panel, values=["Disponible", "Reservado", "Cuarentena"], state="readonly")
        self.combo_estado.current(0)
        self.combo_estado.pack(pady=5)

        tk.Label(left_panel, text="Cantidad:").pack(anchor="w")
        self.entry_cant: tk.Entry = tk.Entry(left_panel)
        self.entry_cant.pack(pady=5)

        tk.Button(left_panel, text="Ejecutar Movimiento", command=self.ejecutar, bg="#d9534f", fg="white").pack(pady=20, fill="x")

        # --- Panel Derecho: Historial (Kardex) ---
        right_panel: tk.Frame = tk.Frame(self)
        right_panel.pack(side="right", fill="both", expand=True, padx=10)
        
        tk.Label(right_panel, text="HISTORIAL DE MOVIMIENTOS", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.tree: ttk.Treeview = ttk.Treeview(right_panel, columns=('Fecha', 'Prod', 'User', 'Tipo', 'Concepto', 'Cant'), show='headings')
        self.tree.heading('Fecha', text='Fecha/Hora')
        self.tree.heading('Prod', text='Producto')
        self.tree.heading('User', text='Usuario')
        self.tree.heading('Tipo', text='Tipo')
        self.tree.heading('Concepto', text='Concepto')
        self.tree.heading('Cant', text='Cant')
        
        self.tree.column('Fecha', width=120)
        self.tree.column('Cant', width=50)
        
        self.tree.pack(fill="both", expand=True)
        self.cargar_historial()

    def cargar_productos_combo(self) -> None:
        """Obtiene productos de la DB y llena el combobox."""
        prods: List[Tuple[Any, ...]] = get_all_products()
        values: List[str] = []
        
        self.map_products.clear() # Limpiar mapa antes de recargar
        
        for p in prods:
            # p[0]: ID, p[1]: Nombre, p[4]: Stock
            display: str = f"{p[1]} (Stock: {p[4]})"
            values.append(display)
            self.map_products[display] = int(p[0])
            
        self.combo_prods['values'] = values

    def cargar_historial(self) -> None:
        """Limpia y recarga el Treeview con el historial de movimientos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        history: List[Tuple[Any, ...]] = get_movements_history()
        for h in history:
            self.tree.insert('', 'end', values=h)

    def ejecutar(self) -> None:
        """Valida entradas y ejecuta la lógica de negocio de entrada/salida."""
        try:
            prod_name: str = self.combo_prods.get()
            
            if prod_name not in self.map_products:
                messagebox.showerror("Error", "Seleccione un producto válido")
                return
            
            prod_id: int = self.map_products[prod_name]
            tipo: str = self.combo_tipo.get()
            concepto: str = self.combo_concepto.get()
            estado: str = self.combo_estado.get()
            qty_str: str = self.entry_cant.get()
            
            if not qty_str.isdigit():
                raise ValueError("La cantidad debe ser un número entero positivo")
            
            qty: int = int(qty_str)
            user: Any = get_current_user() 

            if user is None:
                messagebox.showerror("Error", "Sesión no válida")
                return

            if tipo == "ENTRADA":
                registrar_entrada(prod_id, user.id if hasattr(user, 'id') else user['id'], qty, estado, concept=concepto)
            else:
                registrar_salida(prod_id, user.id if hasattr(user, 'id') else user['id'], qty, estado, concept=concepto)
            
            messagebox.showinfo("Éxito", "Movimiento registrado correctamente")
            
            # Actualización de la UI
            self.cargar_historial()
            self.cargar_productos_combo()
            self.entry_cant.delete(0, tk.END)
            
        except ValueError as ve:
            messagebox.showerror("Error de Validación", str(ve))
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado: {e}")