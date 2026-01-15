from .conexion_db import ConexionDB
from tkinter import messagebox

def crear_tabla():
    conexion = ConexionDB()

    sql = '''
    CREATE TABLE almacen(
        id_product INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre VARCHAR(100),
        precio NUMERIC(10, 2),
        stock INTEGER,
    )'''
    try:
        conexion.cursor.execute(sql)
        conexion.commit()
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

    sql = 'DROP TABLE IF EXISTS almacen'
    try:
        conexion.cursor.execute(sql)
        conexion.cerrar()
        titulo = 'Borrar Registro'
        mensaje = 'La tabla de la base de datos se borro con éxito'
        messagebox.showinfo(titulo, mensaje)
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
        return f'Pelicila[{self.nombre}, {self.precio}, {self.stock}]'

def guadar(product):  # Renombra a guardar en import
    conexion = ConexionDB()
    sql = '''INSERT INTO almacen (nombre, precio, stock) 
             VALUES (?, ?, ?)'''  # ✅ Parámetros seguros
    try:
        conexion.cursor.execute(sql, (product.nombre, product.precio, product.stock))
        conexion.commit()
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
        titulo = 'Conexion al Registro '
        mensaje = 'Crea la tabla en la Base de datos'
        messagebox.showwarning(titulo, mensaje)

    return lista_productos

def editar(product, id_product):
    conexion = ConexionDB()
    sql = '''UPDATE almacen 
             SET nombre = ?, precio = ?, stock = ? 
             WHERE id_product = ?'''  # ✅ Campos correctos + parámetros
    try:
        conexion.cursor.execute(sql, (product.nombre, product.precio, product.stock, id_product))
        conexion.commit()
        conexion.cerrar()
    except Exception as e:
        conexion.cerrar()
        messagebox.showerror('Error', f'Error al editar: {e}')

def eliminar(id_product):
    conexion = ConexionDB()
    sql = 'DELETE FROM almacen WHERE id_product = ?'  # ✅ Parámetro seguro
    try:
        conexion.cursor.execute(sql, (id_product,))
        conexion.commit()
        conexion.cerrar()
    except Exception as e:
        conexion.cerrar()
        messagebox.showerror('Error', f'Error al eliminar: {e}')
#vito