import sqlite3
import os

DB_PATH = os.path.join('data', 'almacen.db')

def get_connection():
    # Asegurar que el directorio data existe
    if not os.path.exists('data'):
        os.makedirs('data')
    return sqlite3.connect(DB_PATH)

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    
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
    # Un producto puede tener stock en diferentes estados
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
    if not cursor.fetchone():
        # En prod usar hashing, aqui texto plano por simplicidad segun requisitos
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'Administrador')")

    conn.commit()
    conn.close()