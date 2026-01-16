import sqlite3
from .connection import get_connection

def execute_query(query, params=(), fetch=False):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
            return result
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error DB: {e}")
        return None
    finally:
        conn.close()

# --- Productos ---
def get_all_products():
    sql = """
    SELECT p.id, p.name, p.barcode, p.category, 
           coalesce(sum(s.quantity), 0) as total_stock, 
           p.location_aisle || '-' || p.location_shelf || '-' || p.location_level as location
    FROM products p
    LEFT JOIN stock s ON p.id = s.product_id
    GROUP BY p.id
    """
    return execute_query(sql, fetch=True)

def insert_product(data):
    sql = '''INSERT INTO products (name, barcode, category, uom, location_aisle, location_shelf, location_level) 
             VALUES (?, ?, ?, ?, ?, ?, ?)'''
    return execute_query(sql, data)

def update_stock(product_id, state, quantity, operation='+'):
    # Verificar si existe registro de stock para ese estado
    check_sql = "SELECT id, quantity FROM stock WHERE product_id=? AND state=?"
    row = execute_query(check_sql, (product_id, state), fetch=True)
    
    if not row:
        if operation == '-': return False # No se puede restar lo que no existe
        # Crear registro inicial
        sql = "INSERT INTO stock (product_id, state, quantity) VALUES (?, ?, ?)"
        execute_query(sql, (product_id, state, quantity))
    else:
        stock_id, current_qty = row[0]
        new_qty = current_qty + quantity if operation == '+' else current_qty - quantity
        if new_qty < 0: return False
        sql = "UPDATE stock SET quantity=? WHERE id=?"
        execute_query(sql, (new_qty, stock_id))
    return True

# --- Movimientos ---
def insert_movement(product_id, user_id, move_type, concept, quantity):
    sql = '''INSERT INTO movements (product_id, user_id, move_type, concept, quantity) 
             VALUES (?, ?, ?, ?, ?)'''
    execute_query(sql, (product_id, user_id, move_type, concept, quantity))

def get_movements_history():
    sql = '''
    SELECT m.timestamp, p.name, u.username, m.move_type, m.concept, m.quantity
    FROM movements m
    JOIN products p ON m.product_id = p.id
    JOIN users u ON m.user_id = u.id
    ORDER BY m.timestamp DESC
    '''
    return execute_query(sql, fetch=True)

# --- Usuarios ---
def get_user_by_credentials(username, password):
    sql = "SELECT id, username, role FROM users WHERE username=? AND password=?"
    result = execute_query(sql, (username, password), fetch=True)
    return result[0] if result else None