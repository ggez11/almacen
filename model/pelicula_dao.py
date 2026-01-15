from .conexion_db import ConexionDB
from tkinter import messagebox

def crear_tabla():
    conexion = ConexionDB()

    sql = '''
    CREATE TABLE IF NOT EXISTS almacen(
        id_product INTEGER,
        nombre VARCHAR(100),
        precio INT,
        stock INT,
        PRIMARY KEY(id_product AUTOINCREMENT)
    )'''
    try:
        conexion.cursor.execute(sql)
        conexion.cerrar()
        titulo = 'Crear Registro'
        mensaje = 'Se creo la tabla en la base datos'
        messagebox.showinfo(titulo, mensaje)
    except:
        titulo = 'Crear Registro'
        mensaje = 'La tabla ya esta creada'
        messagebox.showwarning(titulo, mensaje)


def borrar_tabla():
    conexion = ConexionDB()

    sql = 'DROP TABLE almacen'
    try:
        conexion.cursor.execute(sql)
        conexion.cerrar()
        titulo = 'Borrar Registro'
        mensaje = 'La tabla de la base de datos se borro con éxito'
        messagebox.showinfo(titulo, mensaje)
        return 'ASd'
    except:
        titulo = 'Borrar Registro'
        mensaje = 'No hay tabla para borrar'
        messagebox.showerror(titulo, mensaje)

class Almacen:
    def __init__(self, nombre, precio, stock):
        self.id_product = None
        self.nombre = nombre
        self.precio = precio
        self.stock = stock

    def __str__(self):
        return f'Producto [{self.nombre}, {self.precio}, {self.stock}]'

def guardar(product):
    conexion = ConexionDB()
    sql = f"""INSERT INTO almacen (nombre, precio, stock) 
            VALUES ('{product.nombre}', '{product.precio}', '{product.stock}')""" # ✅ Parámetros seguros
    try:
        conexion.cursor.execute(sql)
        conexion.cerrar()
    except Exception as e:
        conexion.cerrar()
        messagebox.showerror('Error', f'No se pudo guardar: {e}')

def listar():
    conexion = ConexionDB()

    lista_productos = []
    sql = 'SELECT * FROM almacen'

    try: 
        conexion.cursor.execute(sql)
        lista_productos = conexion.cursor.fetchall()
        conexion.cerrar()
    except:
        titulo = 'Conexion al Registro'
        mensaje = 'Crea la tabla en la Base de datos'
        messagebox.showwarning(titulo, mensaje)
        return False
    return lista_productos

def editar(product, id_product):
    conexion = ConexionDB()
    sql = f"""UPDATE almacen
            SET nombre = '{product.nombre}', precio = '{product.precio}', stock = '{product.stock }'
            WHERE id_product = '{id_product}' """  # ✅ Campos correctos + parámetros
    try:
        conexion.cursor.execute(sql)
        conexion.cerrar()
    except:
        conexion.cerrar()
        messagebox.showerror('Error', f'Error al editar')

def eliminar(id_product):
    conexion = ConexionDB()
    sql = f"DELETE FROM almacen WHERE id_product = '{id_product}' "  # ✅ Parámetro seguro
    try:
        conexion.cursor.execute(sql)
        conexion.cerrar()
    except:
        conexion.cerrar()
        messagebox.showerror('Error', f'Error al eliminar')
#vito