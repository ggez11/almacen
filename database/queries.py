import sqlite3
from typing import List, Tuple, Any, Optional, Union, Iterable
from .connection import get_connection

# Tipo personalizado para los resultados de la DB
# Puede ser una lista de tuplas (select), un entero (insert id) o None (error)
QueryResult = Union[List[Tuple[Any, ...]], int, None]

def execute_query(
    query: str, 
    params: Iterable[Any] = (), 
    fetch: bool = False
) -> QueryResult:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            result: List[Tuple[Any, ...]] = cursor.fetchall()
            return result
        conn.commit()
        return int(cursor.lastrowid) if cursor.lastrowid is not None else 0
    except sqlite3.Error as e:
        print(f"Error DB: {e}")
        return None
    finally:
        conn.close()

# --- Productos ---
def get_all_products() -> List[Tuple[Any, ...]]:
    sql = """
    SELECT p.id, p.name, p.barcode, p.category, 
           coalesce(sum(s.quantity), 0) as total_stock, 
           p.location_aisle || '-' || p.location_shelf || '-' || p.location_level as location
    FROM products p
    LEFT JOIN stock s ON p.id = s.product_id
    GROUP BY p.id
    """
    result = execute_query(sql, fetch=True)
    # Casteamos el resultado para asegurar que el editor sepa que es una lista
    return result if isinstance(result, list) else []

def insert_product(data: Tuple[Any, ...]) -> Optional[int]:
    sql = '''INSERT INTO products (name, barcode, category, uom, location_aisle, location_shelf, location_level) 
             VALUES (?, ?, ?, ?, ?, ?, ?)'''
    result = execute_query(sql, data)
    return result if isinstance(result, int) else None

def update_stock(
    product_id: int, 
    state: str, 
    quantity: int, 
    operation: str = '+'
) -> bool:
    check_sql = "SELECT id, quantity FROM stock WHERE product_id=? AND state=?"
    row = execute_query(check_sql, (product_id, state), fetch=True)
    
    # Verificamos que sea una lista y tenga contenido
    if not isinstance(row, list) or not row:
        if operation == '-': return False
        sql = "INSERT INTO stock (product_id, state, quantity) VALUES (?, ?, ?)"
        execute_query(sql, (product_id, state, quantity))
    else:
        stock_id: int = row[0][0]
        current_qty: int = row[0][1]
        new_qty = current_qty + quantity if operation == '+' else current_qty - quantity
        
        if new_qty < 0: return False
        
        sql = "UPDATE stock SET quantity=? WHERE id=?"
        execute_query(sql, (new_qty, stock_id))
    return True

def get_product_stock(product_id: int, state: str) -> int:
    """
    Obtiene la cantidad actual de un producto en un estado específico.
    Si no existe el registro, retorna 0.
    """
    sql: str = "SELECT quantity FROM stock WHERE product_id=? AND state=?"
    result: QueryResult = execute_query(sql, (product_id, state), fetch=True)
    
    if isinstance(result, list) and len(result) > 0:
        # result[0][0] es el valor de la columna 'quantity'
        return int(result[0][0])
    
    return 0

def get_products_simple() -> List[Tuple[int, str]]:
    """
    Retorna una lista simplificada (id, nombre) para llenar selectores/comboboxes.
    """
    sql: str = "SELECT id, name FROM products ORDER BY name ASC"
    result: QueryResult = execute_query(sql, fetch=True)
    
    # Casteamos para asegurar que el tipo de retorno sea el esperado
    if isinstance(result, list):
        return result  # type: ignore
    return []
    
# --- Movimientos ---
def insert_movement(
    product_id: int, 
    user_id: int, 
    move_type: str, 
    concept: str, 
    quantity: int
) -> None:
    sql = '''INSERT INTO movements (product_id, user_id, move_type, concept, quantity) 
             VALUES (?, ?, ?, ?, ?)'''
    execute_query(sql, (product_id, user_id, move_type, concept, quantity))

def get_movements_history() -> List[Tuple[Any, ...]]:
    sql = '''
    SELECT m.timestamp, p.name, u.username, m.move_type, m.concept, m.quantity
    FROM movements m
    JOIN products p ON m.product_id = p.id
    JOIN users u ON m.user_id = u.id
    ORDER BY m.timestamp DESC
    '''
    result = execute_query(sql, fetch=True)
    return result if isinstance(result, list) else []

# --- Usuarios ---
def get_user_by_credentials(username: str, password: str) -> Optional[Tuple[int, str, str]]:
    sql = "SELECT id, username, role FROM users WHERE username=? AND password=?"
    result = execute_query(sql, (username, password), fetch=True)
    
    if isinstance(result, list) and len(result) > 0:
        # Retornamos la primera fila como tupla de (id, nombre, rol)
        return result[0] # type: ignore
    return None
import sqlite3

def delete_product(p_id: int) -> bool:
    """Elimina un producto de la base de datos usando la tabla 'products'."""
    sql = "DELETE FROM products WHERE id = ?"
    # Usamos execute_query para aprovechar la conexión que ya tienen configurada
    result = execute_query(sql, (p_id,))
    return result is not None

def update_product(data: tuple) -> bool:
    """
    Actualiza los datos en la tabla 'products'.
    data debe ser: (nombre, barcode, categoria, ubicacion, id)
    """
    # Nota: Tu tabla usa location_aisle, location_shelf, etc. 
    # Para simplificar, actualizaremos el nombre, barcode y categoría.
    sql = """
        UPDATE products 
        SET name = ?, 
            barcode = ?, 
            category = ?
        WHERE id = ?
    """
    # Ajustamos la data para que coincida con los 4 campos de arriba 
    # (nombre, barcode, categoria, id)
    filtered_data = (data[0], data[1], data[2], data[4])
    
    result = execute_query(sql, filtered_data)
    return result is not None