import sqlite3
import os
from typing import Optional

# El path es una cadena constante
DB_PATH: str = os.path.join('data', 'almacen.db')

def get_connection() -> sqlite3.Connection:
    """
    Establece la conexión con la base de datos SQLite.
    Asegura la existencia del directorio de datos.
    """
    # Asegurar que el directorio data existe
    if not os.path.exists('data'):
        os.makedirs('data')
    
    return sqlite3.connect(DB_PATH)

def initialize_db() -> None:
    """
    Crea las tablas necesarias y el usuario administrador inicial.
    """
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    # Tabla Usuarios (Roles)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL -- 'Administrador', 'Almacenero', 'Consultor'
    )
    ''')

    # Tabla Proveedores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT
    )
    ''')

    # Tabla Productos (Logistica, Categorias, Codigo Barras, UoM)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        barcode TEXT UNIQUE,
        category TEXT,
        subcategory TEXT,
        supplier_id INTEGER,
        uom TEXT, -- Unidad, Caja, Pallet
        location_aisle TEXT,
        location_shelf TEXT,
        location_level TEXT,
        min_stock INTEGER DEFAULT 0,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    )
    ''')

    # Tabla Stock (Estados)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        state TEXT NOT NULL, -- 'Disponible', 'Reservado', 'Cuarentena'
        quantity INTEGER DEFAULT 0,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    ''')

    # Tabla Historial de Movimientos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        user_id INTEGER,
        move_type TEXT, -- 'ENTRADA', 'SALIDA'
        concept TEXT, -- 'Venta', 'Merma', 'Devolucion', 'Compra'
        quantity INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Crear usuario Admin por defecto si no existe
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    # fetchone() puede devolver una tupla o None
    admin_exists: Optional[tuple] = cursor.fetchone()
    
    if not admin_exists:
        # En prod usar hashing, aquí texto plano por simplicidad
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', 'admin', 'Administrador')
        )

    conn.commit()
    conn.close()