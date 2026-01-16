# Frame Movimientos

import tkinter as tk
from tkinter import ttk, messagebox
from database.queries import get_all_products, get_movements_history
from services.inv_manager import registrar_entrada, registrar_salida
from services.auth_service import get_current_user

class MovimientosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # --- Panel Izquierdo: Formulario de Movimiento ---
        left_panel = tk.Frame(self, padx=10, pady=10, bd=2, relief="groove")
        left_panel.pack(side="left", fill="y")
        
        tk.Label(left_panel, text="REGISTRAR MOVIMIENTO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Seleccionar Producto
        tk.Label(left_panel, text="Producto:").pack(anchor="w")
        self.combo_prods = ttk.Combobox(left_panel, width=30)
        self.combo_prods.pack(pady=5)
        self.map_products = {} # Para mapear "Nombre" -> ID
        self.cargar_productos_combo()

        # Tipo Movimiento
        tk.Label(left_panel, text="Tipo:").pack(anchor="w")
        self.combo_tipo = ttk.Combobox(left_panel, values=["ENTRADA", "SALIDA"], state="readonly")
        self.combo_tipo.current(0)
        self.combo_tipo.pack(pady=5)

        # Concepto
        tk.Label(left_panel, text="Concepto:").pack(anchor="w")
        self.combo_concepto = ttk.Combobox(left_panel, values=["Compra", "Venta", "Merma", "Devolucion", "Ajuste"])
        self.combo_concepto.pack(pady=5)
        
        # Estado
        tk.Label(left_panel, text="Estado Stock:").pack(anchor="w")
        self.combo_estado = ttk.Combobox(left_panel, values=["Disponible", "Reservado", "Cuarentena"], state="readonly")
        self.combo_estado.current(0)
        self.combo_estado.pack(pady=5)

        # Cantidad
        tk.Label(left_panel, text="Cantidad:").pack(anchor="w")
        self.entry_cant = tk.Entry(left_panel)
        self.entry_cant.pack(pady=5)

        tk.Button(left_panel, text="Ejecutar Movimiento", command=self.ejecutar, bg="#d9534f", fg="white").pack(pady=20, fill="x")

        # --- Panel Derecho: Historial (Kardex) ---
        right_panel = tk.Frame(self)
        right_panel.pack(side="right", fill="both", expand=True, padx=10)
        
        tk.Label(right_panel, text="HISTORIAL DE MOVIMIENTOS", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.tree = ttk.Treeview(right_panel, columns=('Fecha', 'Prod', 'User', 'Tipo', 'Concepto', 'Cant'), show='headings')
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

    def cargar_productos_combo(self):
        prods = get_all_products()
        values = []
        for p in prods:
            # p[0] es ID, p[1] es Nombre
            display = f"{p[1]} (Stock: {p[4]})"
            values.append(display)
            self.map_products[display] = p[0]
        self.combo_prods['values'] = values

    def cargar_historial(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        history = get_movements_history()
        for h in history:
            self.tree.insert('', 'end', values=h)

    def ejecutar(self):
        try:
            prod_name = self.combo_prods.get()
            if prod_name not in self.map_products:
                messagebox.showerror("Error", "Seleccione un producto válido")
                return
            
            prod_id = self.map_products[prod_name]
            tipo = self.combo_tipo.get()
            concepto = self.combo_concepto.get()
            estado = self.combo_estado.get()
            qty = int(self.entry_cant.get())
            user = get_current_user()

            if tipo == "ENTRADA":
                registrar_entrada(prod_id, user['id'], qty, estado, concept=concepto)
            else:
                registrar_salida(prod_id, user['id'], qty, estado, concept=concepto)
            
            messagebox.showinfo("Éxito", "Movimiento registrado")
            self.cargar_historial()
            self.cargar_productos_combo() # Actualizar stock visual en combo
            
        except ValueError as ve:
            messagebox.showerror("Error de Validación", str(ve))
        except Exception as e:
            messagebox.showerror("Error Crítico", str(e))