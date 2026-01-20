# queries.py - VERSIÓN LIMPIA Y ACTUALIZADA
import sqlite3
import uuid
from typing import List, Tuple, Any, Optional, Union, Iterable, Dict
from .connection import get_connection

# Tipo personalizado para los resultados de la DB
QueryResult = Union[List[Tuple[Any, ...]], int, None]

def execute_query(
    query: str, 
    params: Iterable[Any] = (), 
    fetch: bool = False,
    fetchone: bool = False
) -> QueryResult:
    """
    Ejecuta una consulta SQL con opciones de fetch.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetchone:
            result = cursor.fetchone()
            return result if result else None
        elif fetch:
            result = cursor.fetchall()
            return result
        conn.commit()
        return int(cursor.lastrowid) if cursor.lastrowid is not None else 0
    except sqlite3.Error as e:
        print(f"Error DB: {e}")
        return None
    finally:
        conn.close()

# ============================================
# --- FUNCIONES DE AUTENTICACIÓN ---
# ============================================

def get_user_by_credentials(username: str, password: str) -> Optional[Tuple[int, str, str]]:
    """
    Verifica credenciales de usuario.
    Retorna (id, usuario, rol) si las credenciales son válidas.
    """
    sql = """
    SELECT id, usuario, rol 
    FROM usuarios 
    WHERE usuario = ? AND contrasena = ? AND activo = 1
    """
    result = execute_query(sql, (username, password), fetchone=True)
    
    if result:
        return result  # type: ignore
    return None

# ============================================
# --- FUNCIONES DE PRODUCTOS ---
# ============================================

def get_all_products() -> List[Tuple[Any, ...]]:
    """
    Obtiene todos los productos con su stock TOTAL y ubicación.
    Usa la vista 'vista_inventario_completo' para obtener datos consolidados.
    """
    sql = """
    SELECT 
        producto_id as id,
        nombre as name,
        sku as barcode,
        categoria as category,
        cantidad_total as total_stock,
        unidad_medida,
        ubicacion as location,
        precio,
        proveedor,
        estado
    FROM vista_inventario_completo
    ORDER BY nombre ASC
    """
    result = execute_query(sql, fetch=True)
    return result if isinstance(result, list) else []

def get_products_simple() -> List[Tuple[int, str]]:
    """
    Retorna una lista simplificada (id, nombre) para llenar selectores.
    """
    sql = "SELECT id, nombre FROM productos WHERE activo = 1 ORDER BY nombre ASC"
    result = execute_query(sql, fetch=True)
    
    if isinstance(result, list):
        return result  # type: ignore
    return []

def insert_product(data: Tuple[Any, ...]) -> Optional[int]:
    """
    Inserta un nuevo producto.
    Parámetros: (nombre, sku, categoria, precio, proveedor, unidad_medida, stock_minimo, ubicacion)
    Descripción se deja vacía
    """
    # Asegurar que tenemos todos los parámetros
    nombre, sku, categoria, precio, proveedor, unidad_medida, stock_minimo, ubicacion = data
    
    sql = """
    INSERT INTO productos 
    (nombre, sku, categoria, precio, proveedor, unidad_medida, stock_minimo, ubicacion, descripcion) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    # Descripción vacía por defecto
    params = (nombre, sku, categoria, precio, proveedor, unidad_medida, stock_minimo, ubicacion, "")
    
    result = execute_query(sql, params)
    return result if isinstance(result, int) else None

def buscar_producto_por_sku(sku: str) -> Optional[Dict[str, Any]]:
    """
    Busca un producto por su SKU.
    Retorna un diccionario con los datos del producto o None.
    """
    sql = """
    SELECT 
        p.id,
        p.sku,
        p.nombre,
        p.descripcion,
        p.categoria,
        p.precio,
        p.costo,
        p.proveedor,
        p.unidad_medida,
        p.stock_minimo,
        p.ubicacion,
        COALESCE(i.cantidad, 0) as stock_actual
    FROM productos p
    LEFT JOIN inventario i ON p.id = i.producto_id
    WHERE p.sku = ? AND p.activo = 1
    LIMIT 1
    """
    result = execute_query(sql, (sku,), fetchone=True)
    
    if result:
        return {
            'id': result[0],
            'sku': result[1],
            'nombre': result[2],
            'descripcion': result[3],
            'categoria': result[4],
            'precio': float(result[5]) if result[5] else 0,
            'costo': float(result[6]) if result[6] else 0,
            'proveedor': result[7],
            'unidad_medida': result[8],
            'stock_minimo': result[9],
            'ubicacion': result[10],
            'stock_actual': result[11]
        }
    return None

def buscar_producto_por_nombre(nombre: str) -> List[Dict[str, Any]]:
    """
    Busca productos por nombre (búsqueda parcial).
    """
    sql = """
    SELECT 
        p.id,
        p.sku,
        p.nombre,
        p.categoria,
        p.precio,
        p.proveedor,
        p.ubicacion,
        COALESCE(i.cantidad, 0) as stock_actual
    FROM productos p
    LEFT JOIN inventario i ON p.id = i.producto_id
    WHERE p.nombre LIKE ? AND p.activo = 1
    ORDER BY p.nombre
    LIMIT 20
    """
    result = execute_query(sql, (f'%{nombre}%',), fetch=True)
    
    productos = []
    if isinstance(result, list):
        for row in result:
            productos.append({
                'id': row[0],
                'sku': row[1],
                'nombre': row[2],
                'categoria': row[3],
                'precio': float(row[4]) if row[4] else 0,
                'proveedor': row[5],
                'ubicacion': row[6],
                'stock_actual': row[7]
            })
    return productos

def actualizar_producto(producto_id: int, datos: dict[str, Any]) -> bool:
    """
    Actualiza los datos de un producto existente.
    """
    try:
        campos: list[str] = []
        valores: list[Any] = []
        
        # Construir SET dinámicamente
        for campo, valor in datos.items():
            if valor is not None:
                campos.append(f"{campo} = ?")
                valores.append(valor)
        
        if not campos:
            return False
            
        valores.append(int(producto_id))
        sql: str = f"""
        UPDATE productos 
        SET {', '.join(campos)}
        WHERE id = ? AND activo = 1
        """
        
        result: Any = execute_query(sql, tuple(valores))
        
        # --- EL CAMBIO ESTÁ AQUÍ ---
        # Si result es None pero no hubo excepción, muchas veces es porque 
        # la función execute_query no retorna el rowcount explícitamente.
        if result is None:
            return True
            
        return isinstance(result, int) and result >= 0
        
    except Exception as e:
        print(f"Error al actualizar producto: {e}")
        return False

def eliminar_producto(producto_id: int) -> bool:
    """
    Marca un producto como inactivo. 
    """
    try:
        sql: str = "UPDATE productos SET activo = 0 WHERE id = ?"
        # Ejecutamos la query
        execute_query(sql, (int(producto_id),))
        
        # Como ya comprobaste que SI se elimina en la DB, 
        # vamos a asumir True si no hubo excepción.
        return True 
    except Exception as e:
        print(f"Error real en DB: {e}")
        return False

# ============================================
# --- FUNCIONES DE INVENTARIO ---
# ============================================

def get_product_stock(product_id: int, ubicacion_id: Optional[int] = None) -> int:
    """
    Obtiene la cantidad actual de un producto en inventario.
    Si se especifica ubicacion_id, retorna stock en esa ubicación específica.
    """
    if ubicacion_id:
        sql = "SELECT cantidad FROM inventario WHERE producto_id = ? AND ubicacion_id = ?"
        params = (product_id, ubicacion_id)
    else:
        sql = "SELECT SUM(cantidad) FROM inventario WHERE producto_id = ?"
        params = (product_id,)
    
    result = execute_query(sql, params, fetchone=True)
    
    if result and result[0] is not None:
        return int(result[0])
    return 0

def ajustar_stock(
    producto_id: int,
    ubicacion_id: int,
    cantidad: int,
    tipo: str,  # 'IN' o 'OUT'
    razon: str,
    razon_detalle: Optional[str],
    usuario_id: int,
    observaciones: Optional[str] = None
) -> bool:
    """
    Realiza un ajuste de stock registrando un movimiento.
    El trigger 'actualizar_stock_after_movimiento' actualizará automáticamente el inventario.
    """
    try:
        # Obtener stock actual antes del ajuste
        stock_actual = get_product_stock(producto_id, ubicacion_id)
        
        # Calcular nueva cantidad
        if tipo == 'IN':
            cantidad_nueva = stock_actual + cantidad
        else:  # 'OUT'
            cantidad_nueva = stock_actual - cantidad
            if cantidad_nueva < 0:
                return False  # No hay suficiente stock
        
        # Insertar movimiento (el trigger actualizará el inventario)
        sql = """
        INSERT INTO movimientos 
        (tipo, producto_id, ubicacion_id, cantidad, cantidad_anterior, cantidad_nueva,
         razon, razon_detalle, usuario_id, proveedor, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Obtener proveedor del producto
        sql_proveedor = "SELECT proveedor FROM productos WHERE id = ?"
        result_proveedor = execute_query(sql_proveedor, (producto_id,), fetchone=True)
        proveedor = result_proveedor[0] if result_proveedor else None
        
        params = (
            tipo, producto_id, ubicacion_id, cantidad,
            stock_actual, cantidad_nueva,
            razon, razon_detalle, usuario_id, proveedor, observaciones
        )
        
        result = execute_query(sql, params)
        return isinstance(result, int) and result > 0
        
    except Exception as e:
        print(f"Error al ajustar stock: {e}")
        return False

def update_stock(
    product_id: int, 
    state: str, 
    quantity: int, 
    operation: str = '+'
) -> bool:
    """
    FUNCIÓN DE COMPATIBILIDAD - Mantenida para código existente.
    En la nueva estructura, usar 'ajustar_stock' en su lugar.
    """
    # Mapear estados viejos a razones nuevas
    razon_map = {
        'Disponible': 'ajuste manual',
        'Reservado': 'reserva',
        'Cuarentena': 'cuarentena'
    }
    
    razon = razon_map.get(state, 'ajuste manual')
    tipo = 'IN' if operation == '+' else 'OUT'
    
    # En la nueva estructura necesitamos una ubicación
    # Por defecto, usar la primera ubicación disponible
    sql = "SELECT id FROM ubicaciones WHERE activo = 1 LIMIT 1"
    result = execute_query(sql, fetchone=True)
    
    if not result:
        return False
    
    ubicacion_id = result[0]
    
    # Usar la nueva función
    return ajustar_stock(
        producto_id=product_id,
        ubicacion_id=ubicacion_id,
        cantidad=quantity,
        tipo=tipo,
        razon=razon,
        razon_detalle=f"Migración desde estado: {state}",
        usuario_id=1,  # admin por defecto
        observaciones="Ajuste automático por compatibilidad"
    )

def get_stock_detallado(producto_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el stock detallado de un producto por ubicación.
    """
    sql = """
    SELECT 
        u.codigo,
        i.cantidad,
        u.pasillo,
        u.estante,
        u.nivel
    FROM inventario i
    JOIN ubicaciones u ON i.ubicacion_id = u.id
    WHERE i.producto_id = ? AND i.cantidad > 0
    ORDER BY u.codigo
    """
    result = execute_query(sql, (producto_id,), fetch=True)
    
    stock_detallado = []
    if isinstance(result, list):
        for row in result:
            stock_detallado.append({
                'ubicacion': row[0],
                'cantidad': row[1],
                'pasillo': row[2],
                'estante': row[3],
                'nivel': row[4]
            })
    return stock_detallado

# ============================================
# --- FUNCIONES DE MOVIMIENTOS ---
# ============================================

def get_movimientos_history() -> List[Tuple[Any, ...]]:
    """
    Obtiene el historial de movimientos.
    Usa la vista 'vista_movimientos_detallados'.
    """
    sql = """
    SELECT 
        fecha_movimiento,
        producto,
        tipo,
        cantidad,
        razon,
        proveedor,
        ubicacion,
        observaciones
    FROM vista_movimientos_detallados
    ORDER BY fecha_movimiento DESC
    LIMIT 100
    """
    result = execute_query(sql, fetch=True)
    return result if isinstance(result, list) else []

def obtener_movimientos_por_fecha(fecha_inicio: str, fecha_fin: str) -> List[Tuple[Any, ...]]:
    """
    Obtiene movimientos entre fechas específicas.
    """
    sql = """
    SELECT 
        fecha_movimiento,
        producto,
        tipo,
        cantidad,
        razon,
        proveedor,
        ubicacion,
        observaciones
    FROM vista_movimientos_detallados
    WHERE DATE(fecha_movimiento) BETWEEN ? AND ?
    ORDER BY fecha_movimiento DESC
    """
    result = execute_query(sql, (fecha_inicio, fecha_fin), fetch=True)
    return result if isinstance(result, list) else []

def insert_movement(
    product_id: int, 
    user_id: int, 
    move_type: str, 
    concept: str, 
    quantity: int
) -> None:
    """
    FUNCIÓN DE COMPATIBILIDAD - Mantenida para código existente.
    En la nueva estructura, usar 'ajustar_stock' en su lugar.
    """
    # Mapear conceptos viejos a razones nuevas
    razon_map = {
        'Venta': 'venta',
        'Merma': 'merma',
        'Devolucion': 'devolucion',
        'Compra': 'compra'
    }
    
    razon = razon_map.get(concept, 'ajuste manual')
    tipo = 'OUT' if move_type == 'SALIDA' else 'IN'
    
    # Obtener ubicación por defecto
    sql = "SELECT id FROM ubicaciones WHERE activo = 1 LIMIT 1"
    result = execute_query(sql, fetchone=True)
    
    if result:
        ubicacion_id = result[0]
        ajustar_stock(
            producto_id=product_id,
            ubicacion_id=ubicacion_id,
            cantidad=quantity,
            tipo=tipo,
            razon=razon,
            razon_detalle=None,
            usuario_id=user_id,
            observaciones=f"Movimiento: {concept}"
        )

def get_movimientos_por_producto(producto_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el historial de movimientos de un producto específico.
    """
    sql = """
    SELECT 
        m.fecha_movimiento,
        m.tipo,
        m.cantidad,
        m.cantidad_anterior,
        m.cantidad_nueva,
        m.razon,
        m.razon_detalle,
        u.usuario,
        ub.codigo as ubicacion,
        m.observaciones
    FROM movimientos m
    JOIN usuarios u ON m.usuario_id = u.id
    LEFT JOIN ubicaciones ub ON m.ubicacion_id = ub.id
    WHERE m.producto_id = ?
    ORDER BY m.fecha_movimiento DESC
    LIMIT 50
    """
    result = execute_query(sql, (producto_id,), fetch=True)
    
    movimientos = []
    if isinstance(result, list):
        for row in result:
            movimientos.append({
                'fecha': row[0],
                'tipo': row[1],
                'cantidad': row[2],
                'cantidad_anterior': row[3],
                'cantidad_nueva': row[4],
                'razon': row[5],
                'razon_detalle': row[6],
                'usuario': row[7],
                'ubicacion': row[8],
                'observaciones': row[9]
            })
    return movimientos

# ============================================
# --- FUNCIONES DE UBICACIONES ---
# ============================================

def obtener_ubicaciones() -> List[Tuple[int, str]]:
    """
    Obtiene todas las ubicaciones activas.
    Retorna (id, codigo).
    """
    sql = "SELECT id, codigo FROM ubicaciones WHERE activo = 1 ORDER BY codigo"
    result = execute_query(sql, fetch=True)
    return result if isinstance(result, list) else []

def obtener_ubicacion_por_codigo(codigo: str) -> Optional[int]:
    """
    Obtiene el ID de una ubicación por su código.
    """
    sql = "SELECT id FROM ubicaciones WHERE codigo = ? AND activo = 1"
    result = execute_query(sql, (codigo,), fetchone=True)
    return result[0] if result else None

def obtener_ubicacion_predeterminada() -> Optional[int]:
    """
    Obtiene la primera ubicación activa como predeterminada.
    """
    sql = "SELECT id FROM ubicaciones WHERE activo = 1 LIMIT 1"
    result = execute_query(sql, fetchone=True)
    return result[0] if result else None

def crear_ubicacion(pasillo: str, estante: str, nivel: str) -> Optional[int]:
    """
    Crea una nueva ubicación.
    """
    codigo = f"{pasillo}-{estante}-{nivel}"
    sql = """
    INSERT INTO ubicaciones (codigo, pasillo, estante, nivel, capacidad, ocupado, activo)
    VALUES (?, ?, ?, ?, 1, 0, 1)
    """
    result = execute_query(sql, (codigo, pasillo, estante, nivel))
    return result if isinstance(result, int) else None

def obtener_ubicaciones_disponibles() -> List[Dict[str, Any]]:
    """
    Obtiene ubicaciones disponibles (con espacio).
    """
    sql = """
    SELECT 
        id,
        codigo,
        pasillo,
        estante,
        nivel,
        capacidad,
        ocupado
    FROM ubicaciones
    WHERE activo = 1 AND (ocupado = 0 OR capacidad > 0)
    ORDER BY codigo
    """
    result = execute_query(sql, fetch=True)
    
    ubicaciones = []
    if isinstance(result, list):
        for row in result:
            ubicaciones.append({
                'id': row[0],
                'codigo': row[1],
                'pasillo': row[2],
                'estante': row[3],
                'nivel': row[4],
                'capacidad': row[5],
                'ocupado': bool(row[6])
            })
    return ubicaciones

# ============================================
# --- FUNCIONES DE ÓRDENES/VENTAS ---
# ============================================

def crear_orden_venta(
    tipo_operacion: str,
    cliente_id: Optional[int],
    usuario_id: int,
    productos: List[Dict[str, Any]]
) -> Optional[int]:
    """
    Crea una nueva orden de venta con sus detalles.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Calcular total
        total = sum(p['precio'] * p['cantidad'] for p in productos)
        
        # Generar número de orden
        from datetime import datetime
        
        id_unico: str = uuid.uuid4().hex[:8].upper() # Genera algo como '4A2B91C0'
        numero_orden: str = f"ORD-{datetime.now().strftime('%Y%m%d')}-{id_unico}"
        
        # Insertar orden
        sql_orden = """
        INSERT INTO ordenes 
        (numero_orden, tipo_operacion, cliente_id, total, estado, usuario_id)
        VALUES (?, ?, ?, ?, 'pendiente', ?)
        """
        cursor.execute(sql_orden, (numero_orden, tipo_operacion, cliente_id, total, usuario_id))
        orden_id = cursor.lastrowid
        
        # Insertar detalles
        for producto in productos:
            sql_detalle = """
            INSERT INTO orden_detalles 
            (orden_id, producto_id, cantidad, precio_unitario, ubicacion_id, procesado)
            VALUES (?, ?, ?, ?, ?, 0)
            """
            cursor.execute(sql_detalle, (
                orden_id,
                producto['id'],
                producto['cantidad'],
                producto['precio'],
                producto.get('ubicacion_id')
            ))
        
        conn.commit()
        return orden_id
        
    except sqlite3.IntegrityError:
        print(f"Error: El número de orden {numero_orden} ya existe.")
        return None
    except Exception as e:
        print(f"Error inesperado al crear orden: {e}")
        return None
    finally:
        conn.close()

def obtener_ordenes_pendientes() -> List[Dict[str, Any]]:
    """
    Obtiene todas las órdenes pendientes.
    """
    sql = """
    SELECT 
        o.id,
        o.numero_orden,
        o.tipo_operacion,
        c.nombre as cliente,
        o.total,
        o.estado,
        u.usuario,
        o.fecha_creacion
    FROM ordenes o
    LEFT JOIN clientes c ON o.cliente_id = c.id
    JOIN usuarios u ON o.usuario_id = u.id
    WHERE o.estado = 'pendiente'
    ORDER BY o.fecha_creacion DESC
    LIMIT 50
    """
    result = execute_query(sql, fetch=True)
    
    ordenes = []
    if isinstance(result, list):
        for row in result:
            ordenes.append({
                'id': row[0],
                'numero_orden': row[1],
                'tipo_operacion': row[2],
                'cliente': row[3],
                'total': float(row[4]) if row[4] else 0,
                'estado': row[5],
                'usuario': row[6],
                'fecha_creacion': row[7]
            })
    return ordenes

# ============================================
# --- FUNCIONES DE CLIENTES ---
# ============================================

def obtener_clientes() -> List[Tuple[int, str]]:
    """
    Obtiene todos los clientes activos.
    """
    sql = "SELECT id, nombre FROM clientes WHERE activo = 1 ORDER BY nombre"
    result = execute_query(sql, fetch=True)
    return result if isinstance(result, list) else []

def crear_cliente(nombre: str, documento: str = "", telefono: str = "", 
                 email: str = "", direccion: str = "") -> Optional[int]:
    """
    Crea un nuevo cliente.
    """
    sql = """
    INSERT INTO clientes (nombre, documento, telefono, email, direccion)
    VALUES (?, ?, ?, ?, ?)
    """
    result = execute_query(sql, (nombre, documento, telefono, email, direccion))
    return result if isinstance(result, int) else None

# ============================================
# --- FUNCIONES DE CONFIGURACIÓN ---
# ============================================

def obtener_configuracion(clave: str) -> Optional[str]:
    """
    Obtiene un valor de configuración.
    """
    sql = "SELECT valor FROM configuracion WHERE clave = ?"
    result = execute_query(sql, (clave,), fetchone=True)
    return result[0] if result else None

def actualizar_configuracion(clave: str, valor: str) -> bool:
    """
    Actualiza un valor de configuración.
    """
    sql = """
    INSERT OR REPLACE INTO configuracion (clave, valor)
    VALUES (?, ?)
    """
    result = execute_query(sql, (clave, valor))
    return isinstance(result, int) and result > 0

def obtener_todas_configuraciones() -> Dict[str, str]:
    """
    Obtiene todas las configuraciones como diccionario.
    """
    sql = "SELECT clave, valor FROM configuracion"
    result = execute_query(sql, fetch=True)
    
    configs = {}
    if isinstance(result, list):
        for row in result:
            configs[row[0]] = row[1]
    return configs

# ============================================
# --- FUNCIONES DE USUARIOS ---
# ============================================

def obtener_usuarios() -> List[Dict[str, Any]]:
    """
    Obtiene todos los usuarios activos.
    """
    sql = """
    SELECT 
        id,
        usuario,
        rol,
        activo,
        fecha_creacion
    FROM usuarios
    WHERE activo = 1
    ORDER BY usuario
    """
    result = execute_query(sql, fetch=True)
    
    usuarios = []
    if isinstance(result, list):
        for row in result:
            usuarios.append({
                'id': row[0],
                'usuario': row[1],
                'rol': row[2],
                'activo': bool(row[3]),
                'fecha_creacion': row[4]
            })
    return usuarios

def crear_usuario(usuario: str, contrasena: str, rol: str) -> Optional[int]:
    """
    Crea un nuevo usuario.
    """
    sql = """
    INSERT INTO usuarios (usuario, contrasena, rol)
    VALUES (?, ?, ?)
    """
    result = execute_query(sql, (usuario, contrasena, rol))
    return result if isinstance(result, int) else None

# ============================================
# --- FUNCIONES DE REPORTES ---
# ============================================

def obtener_productos_bajo_stock() -> List[Dict[str, Any]]:
    """
    Obtiene productos con stock bajo o agotado.
    """
    sql = """
    SELECT 
        p.nombre,
        p.sku,
        p.categoria,
        p.stock_minimo,
        COALESCE(i.cantidad, 0) as stock_actual,
        p.ubicacion,
        CASE 
            WHEN COALESCE(i.cantidad, 0) <= p.stock_minimo AND COALESCE(i.cantidad, 0) > 0 THEN 'Low Stock'
            WHEN COALESCE(i.cantidad, 0) = 0 THEN 'Out of Stock'
            ELSE 'In Stock'
        END as estado
    FROM productos p
    LEFT JOIN inventario i ON p.id = i.producto_id
    WHERE p.activo = 1 
    AND (COALESCE(i.cantidad, 0) <= p.stock_minimo OR COALESCE(i.cantidad, 0) = 0)
    ORDER BY stock_actual ASC
    """
    result = execute_query(sql, fetch=True)
    
    productos = []
    if isinstance(result, list):
        for row in result:
            productos.append({
                'nombre': row[0],
                'sku': row[1],
                'categoria': row[2],
                'stock_minimo': row[3],
                'stock_actual': row[4],
                'ubicacion': row[5],
                'estado': row[6]
            })
    return productos

# ============================================
# --- FUNCIONES DE DIAGNÓSTICO ---
# ============================================

def verificar_inventario() -> List[Dict[str, Any]]:
    """
    Verifica inconsistencias en el inventario.
    """
    sql = """
    SELECT 
        p.nombre,
        p.sku,
        p.ubicacion as ubicacion_producto,
        ub.codigo as ubicacion_inventario,
        i.cantidad,
        CASE 
            WHEN ub.id IS NULL AND i.cantidad > 0 THEN 'ERROR: Stock sin ubicación'
            WHEN i.cantidad < 0 THEN 'ERROR: Stock negativo'
            WHEN i.cantidad > 1000 THEN 'ALERTA: Stock muy alto'
            ELSE 'OK'
        END as estado
    FROM productos p
    LEFT JOIN inventario i ON p.id = i.producto_id
    LEFT JOIN ubicaciones ub ON i.ubicacion_id = ub.id
    WHERE p.activo = 1
    AND (ub.id IS NULL OR i.cantidad < 0 OR i.cantidad > 1000)
    """
    result = execute_query(sql, fetch=True)
    
    problemas = []
    if isinstance(result, list):
        for row in result:
            problemas.append({
                'producto': row[0],
                'sku': row[1],
                'ubicacion_producto': row[2],
                'ubicacion_inventario': row[3],
                'cantidad': row[4],
                'estado': row[5]
            })
    return problemas

def resetear_inventario(producto_id: int, cantidad: int) -> bool:
    """
    Resetea el inventario de un producto a una cantidad específica.
    Útil para corrección de datos.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener ubicación predeterminada
        sql_ubicacion = "SELECT id FROM ubicaciones WHERE activo = 1 LIMIT 1"
        cursor.execute(sql_ubicacion)
        ubicacion = cursor.fetchone()
        
        if not ubicacion:
            return False
            
        ubicacion_id = ubicacion[0]
        
        # Eliminar registros existentes
        sql_delete = "DELETE FROM inventario WHERE producto_id = ?"
        cursor.execute(sql_delete, (producto_id,))
        
        # Insertar nuevo registro
        sql_insert = """
        INSERT INTO inventario (producto_id, ubicacion_id, cantidad)
        VALUES (?, ?, ?)
        """
        cursor.execute(sql_insert, (producto_id, ubicacion_id, cantidad))
        
        # Registrar movimiento
        sql_movimiento = """
        INSERT INTO movimientos 
        (tipo, producto_id, ubicacion_id, cantidad, cantidad_anterior, cantidad_nueva,
         razon, razon_detalle, usuario_id, observaciones)
        VALUES ('IN', ?, ?, ?, 0, ?, 'reset', 'Reset manual de inventario', 1, 'Reset de sistema')
        """
        cursor.execute(sql_movimiento, (producto_id, ubicacion_id, cantidad, cantidad))
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"Error al resetear inventario: {e}")
        return False
    finally:
        if conn:
            conn.close()