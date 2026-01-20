# database/connection.py - VERSIÓN ACTUALIZADA Y SIMPLIFICADA
import sqlite3
import os
from typing import Optional

DB_PATH: str = os.path.join('data', 'almacen.db')

def get_connection() -> sqlite3.Connection:
    """
    Establece la conexión con la base de datos SQLite.
    Asegura la existencia del directorio de datos.
    """
    if not os.path.exists('data'):
        os.makedirs('data')
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_db() -> None:
    """
    Crea las tablas necesarias según los módulos existentes.
    """
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    
    # ============================================
    # 1. TABLAS ESENCIALES
    # ============================================
    
    # Tabla usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        contrasena TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('Almacenero', 'Administrador', 'Consultor')),
        activo BOOLEAN DEFAULT 1,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Tabla productos (CON UBICACIÓN Y PROVEEDOR)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        categoria TEXT,
        precio DECIMAL(10,2) DEFAULT 0,
        costo DECIMAL(10,2) DEFAULT 0,
        proveedor TEXT,
        unidad_medida TEXT DEFAULT 'Units',
        stock_minimo INTEGER DEFAULT 0,
        ubicacion TEXT DEFAULT 'Sin ubicación',
        activo BOOLEAN DEFAULT 1,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Tabla ubicaciones
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ubicaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        pasillo TEXT NOT NULL,
        estante TEXT NOT NULL,
        nivel TEXT NOT NULL,
        capacidad INTEGER DEFAULT 1,
        ocupado BOOLEAN DEFAULT 0,
        activo BOOLEAN DEFAULT 1
    )
    ''')

    # Tabla clientes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        documento TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        activo BOOLEAN DEFAULT 1,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Tabla configuracion
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS configuracion (
        clave TEXT PRIMARY KEY,
        valor TEXT,
        descripcion TEXT
    )
    ''')

    # Tabla inventario
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        ubicacion_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id) ON DELETE CASCADE,
        UNIQUE(producto_id, ubicacion_id)
    )
    ''')

    # Tabla ordenes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ordenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_orden TEXT UNIQUE NOT NULL,
        tipo_operacion TEXT NOT NULL CHECK(tipo_operacion IN ('Venta Directa', 'Pedido Web', 'Transferencia')),
        cliente_id INTEGER,
        total DECIMAL(10,2) DEFAULT 0,
        estado TEXT DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'completada', 'cancelada')),
        usuario_id INTEGER NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_completada TIMESTAMP,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')

    # Tabla orden_detalles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orden_detalles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario DECIMAL(10,2),
        ubicacion_id INTEGER,
        procesado BOOLEAN DEFAULT 0,
        FOREIGN KEY (orden_id) REFERENCES ordenes(id) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES productos(id),
        FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id)
    )
    ''')

    # Tabla movimientos (ACTUALIZADA para incluir proveedor)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL CHECK(tipo IN ('IN', 'OUT')),
        producto_id INTEGER NOT NULL,
        ubicacion_id INTEGER,
        cantidad INTEGER NOT NULL,
        cantidad_anterior INTEGER,
        cantidad_nueva INTEGER,
        razon TEXT NOT NULL,
        razon_detalle TEXT,
        usuario_id INTEGER NOT NULL,
        proveedor TEXT,  -- AÑADIDO para compatibilidad con movimientos.py
        referencia TEXT,
        observaciones TEXT,
        fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (producto_id) REFERENCES productos(id),
        FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')

    # ============================================
    # 2. TRIGGERS ESENCIALES
    # ============================================
    
    # Trigger para actualizar stock después de movimiento
    cursor.execute("DROP TRIGGER IF EXISTS actualizar_stock_after_movimiento")
    cursor.execute('''
    CREATE TRIGGER actualizar_stock_after_movimiento
        AFTER INSERT ON movimientos
        FOR EACH ROW
        BEGIN
            -- Entrada (IN)
            UPDATE inventario 
            SET cantidad = cantidad + NEW.cantidad
            WHERE producto_id = NEW.producto_id 
            AND ubicacion_id = NEW.ubicacion_id
            AND NEW.tipo = 'IN'
            AND NEW.ubicacion_id IS NOT NULL;
            
            -- Salida (OUT)
            UPDATE inventario 
            SET cantidad = cantidad - NEW.cantidad
            WHERE producto_id = NEW.producto_id 
            AND ubicacion_id = NEW.ubicacion_id
            AND NEW.tipo = 'OUT'
            AND NEW.ubicacion_id IS NOT NULL
            AND cantidad >= NEW.cantidad;
            
            -- Crear registro si no existe para entradas
            INSERT OR IGNORE INTO inventario (producto_id, ubicacion_id, cantidad)
            SELECT NEW.producto_id, NEW.ubicacion_id, NEW.cantidad
            WHERE NEW.tipo = 'IN' 
            AND NEW.ubicacion_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM inventario 
                WHERE producto_id = NEW.producto_id 
                AND ubicacion_id = NEW.ubicacion_id
            );
        END;
    ''')

    # Trigger para actualizar ocupación de ubicación
    cursor.execute("DROP TRIGGER IF EXISTS actualizar_ocupacion_ubicacion")
    cursor.execute('''
    CREATE TRIGGER actualizar_ocupacion_ubicacion
    AFTER UPDATE OF cantidad ON inventario
    FOR EACH ROW
    BEGIN
        UPDATE ubicaciones
        SET ocupado = CASE 
            WHEN NEW.cantidad > 0 THEN 1 
            ELSE 0 
        END
        WHERE id = NEW.ubicacion_id;
    END;
    ''')

    # ============================================
    # 3. VISTAS ESENCIALES (ACTUALIZADAS)
    # ============================================
    
    # Vista inventario completo (para inventario.py)
    cursor.execute("DROP VIEW IF EXISTS vista_inventario_completo")
    cursor.execute('''
    CREATE VIEW vista_inventario_completo AS
        SELECT 
            p.id as producto_id,
            p.sku,
            p.nombre,
            p.descripcion,
            p.categoria,
            p.precio,
            p.unidad_medida,
            p.costo,
            p.proveedor,
            p.ubicacion,
            
            COALESCE(SUM(i.cantidad), 0) as cantidad_total,
            
            CASE 
                WHEN COALESCE(SUM(i.cantidad), 0) <= p.stock_minimo 
                    AND COALESCE(SUM(i.cantidad), 0) > 0 THEN 'Low Stock'
                WHEN COALESCE(SUM(i.cantidad), 0) = 0 THEN 'Out of Stock'
                ELSE 'In Stock'
            END as estado
            
        FROM productos p
        LEFT JOIN inventario i ON p.id = i.producto_id
        WHERE p.activo = 1
        GROUP BY p.id, p.sku, p.nombre, p.descripcion, p.categoria, 
            p.precio, p.unidad_medida, p.costo, p.proveedor, p.ubicacion, p.stock_minimo;
    ''')

    # Vista movimientos detallados (ACTUALIZADA para incluir proveedor)
    cursor.execute("DROP VIEW IF EXISTS vista_movimientos_detallados")
    cursor.execute('''
    CREATE VIEW vista_movimientos_detallados AS
    SELECT 
        m.fecha_movimiento,
        p.nombre as producto,
        p.sku,
        CASE m.tipo
            WHEN 'IN' THEN '↑ IN'
            WHEN 'OUT' THEN '↓ OUT'
            ELSE m.tipo
        END as tipo,
        m.cantidad,
        m.razon,
        m.razon_detalle,
        COALESCE(m.proveedor, p.proveedor) as proveedor,  -- Prioriza proveedor del movimiento
        u.usuario,
        ub.codigo as ubicacion,
        m.observaciones
    FROM movimientos m
    JOIN productos p ON m.producto_id = p.id
    JOIN usuarios u ON m.usuario_id = u.id
    LEFT JOIN ubicaciones ub ON m.ubicacion_id = ub.id
    ORDER BY m.fecha_movimiento DESC;
    ''')

    # ============================================
    # 4. DATOS INICIALES ESENCIALES
    # ============================================
    
    # Usuarios por defecto
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios_existen = cursor.fetchone()[0] > 0
    
    if not usuarios_existen:
        usuarios_iniciales = [
            ('admin', 'admin123', 'Administrador'),
            ('almacen', 'almacen123', 'Almacenero'),
            ('consulta', 'consulta123', 'Consultor')
        ]
        
        cursor.executemany(
            "INSERT INTO usuarios (usuario, contrasena, rol) VALUES (?, ?, ?)",
            usuarios_iniciales
        )
    
    # Configuraciones básicas
    configuraciones = [
        ('empresa_nombre', 'LogiStock Pro', 'Nombre de la empresa'),
        ('moneda', '$', 'Símbolo de moneda'),
        ('decimales', '2', 'Decimales para precios'),
        ('dias_alerta_caducidad', '30', 'Días para alerta de caducidad'),
        ('porcentaje_stock_minimo', '10', 'Porcentaje para stock mínimo automático')
    ]
    
    for clave, valor, descripcion in configuraciones:
        cursor.execute(
            "SELECT COUNT(*) FROM configuracion WHERE clave = ?",
            (clave,)
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO configuracion (clave, valor, descripcion) VALUES (?, ?, ?)",
                (clave, valor, descripcion)
            )
    
    # Ubicaciones de ejemplo
    ubicaciones_ejemplo = [
        ('3-2-5', '3', '2', '5', 10),
        ('7-7-7', '7', '7', '7', 10),
        ('asd-asd-asd', 'asd', 'asd', 'asd', 10),
        ('1-1-1', '1', '1', '1', 10),
        ('2-2-2', '2', '2', '2', 10)
    ]
    
    for codigo, pasillo, estante, nivel, capacidad in ubicaciones_ejemplo:
        cursor.execute(
            "SELECT COUNT(*) FROM ubicaciones WHERE codigo = ?",
            (codigo,)
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO ubicaciones (codigo, pasillo, estante, nivel, capacidad) VALUES (?, ?, ?, ?, ?)",
                (codigo, pasillo, estante, nivel, capacidad)
            )

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada con estructura actualizada")

# Función de compatibilidad (mantenida para código existente)
def create_tables() -> None:
    """Función alias para initialize_db() - mantenida para compatibilidad."""
    initialize_db()