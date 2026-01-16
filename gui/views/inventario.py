# Frame Inventario
import tkinter as tk
from tkinter import ttk, messagebox
from database.queries import insert_product, get_all_products

class InventarioView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.label_titulo = tk.Label(self, text="GESTIÓN DE PRODUCTOS", font=('Calibri', 16, 'bold'))
        self.label_titulo.pack(pady=10)

        # Frame para formulario
        self.frame_form = tk.Frame(self)
        self.frame_form.pack(pady=10)

        self.campos_product()
        self.tabla_producto()
        self.cargar_datos()

    def campos_product(self):
        # Labels y Entries organizados
        # Fila 0: Nombre y Codigo
        tk.Label(self.frame_form, text="Nombre Prod:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_nombre = tk.Entry(self.frame_form, width=30)
        self.entry_nombre.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.frame_form, text="Cód. Barras:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_barcode = tk.Entry(self.frame_form, width=20)
        self.entry_barcode.grid(row=0, column=3, padx=5, pady=5)
        
        # Simulación de lectura de codigo: Al dar enter en este campo
        self.entry_barcode.bind('<Return>', lambda event: print("Buscando producto..."))

        # Fila 1: Categoria y UoM
        tk.Label(self.frame_form, text="Categoría:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_cat = tk.Entry(self.frame_form, width=30)
        self.entry_cat.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.frame_form, text="U. Medida:").grid(row=1, column=2, padx=5, pady=5)
        self.combo_uom = ttk.Combobox(self.frame_form, values=["Unidad", "Caja", "Pallet"], width=17)
        self.combo_uom.grid(row=1, column=3, padx=5, pady=5)

        # Fila 2: Ubicación
        tk.Label(self.frame_form, text="Ubicación (Pas-Est-Niv):").grid(row=2, column=0, padx=5, pady=5)
        
        frame_loc = tk.Frame(self.frame_form)
        frame_loc.grid(row=2, column=1, columnspan=3, sticky="w")
        
        self.entry_pasillo = tk.Entry(frame_loc, width=5)
        self.entry_pasillo.pack(side="left")
        tk.Label(frame_loc, text="-").pack(side="left")
        self.entry_estante = tk.Entry(frame_loc, width=5)
        self.entry_estante.pack(side="left")
        tk.Label(frame_loc, text="-").pack(side="left")
        self.entry_nivel = tk.Entry(frame_loc, width=5)
        self.entry_nivel.pack(side="left")

        # Botones
        self.boton_guardar = tk.Button(self.frame_form, text="Crear Producto", command=self.guardar_datos, bg="#1658A2", fg="white")
        self.boton_guardar.grid(row=3, column=0, columnspan=4, pady=15, sticky="we")

    def tabla_producto(self):
        self.tree = ttk.Treeview(self, columns=('Nombre', 'Barcode', 'Cat', 'Stock', 'Ubicacion'), show='headings')
        self.tree.heading('Nombre', text='Nombre')
        self.tree.heading('Barcode', text='Código')
        self.tree.heading('Cat', text='Categoría')
        self.tree.heading('Stock', text='Stock Total')
        self.tree.heading('Ubicacion', text='Ubicación')
        
        self.tree.column('Nombre', width=200)
        self.tree.column('Barcode', width=100)
        self.tree.column('Stock', width=80)
        
        self.tree.pack(fill="both", expand=True, padx=10)

    def cargar_datos(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Traer de BD
        products = get_all_products() # Retorna lista de tuplas
        if products:
            for p in products:
                # p = (id, name, barcode, category, stock, location)
                self.tree.insert('', 'end', values=(p[1], p[2], p[3], p[4], p[5]))

    def guardar_datos(self):
        # Recolectar datos
        data = (
            self.entry_nombre.get(),
            self.entry_barcode.get(),
            self.entry_cat.get(),
            self.combo_uom.get(),
            self.entry_pasillo.get(),
            self.entry_estante.get(),
            self.entry_nivel.get()
        )
        
        # Validacion basica
        if not data[0] or not data[1]:
            messagebox.showwarning("Faltan datos", "Nombre y Código son obligatorios")
            return

        res = insert_product(data)
        if res:
            messagebox.showinfo("Éxito", "Producto creado correctamente")
            self.cargar_datos()
            # Limpiar campos (opcional)
        else:
            messagebox.showerror("Error", "No se pudo guardar (¿Código duplicado?)")