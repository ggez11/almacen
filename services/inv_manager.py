from typing import Literal
from database.queries import update_stock, insert_movement

State = Literal["Disponible", "Cuarentena", "Dañado"]
MovementType = Literal["ENTRADA", "SALIDA"]

def registrar_entrada(
    product_id: int, 
    user_id: int, 
    quantity: int, 
    state: State, 
    concept: str = "Compra"
) -> bool:
    """
    Aumenta el stock físico y registra el movimiento en el historial.
    """
    # 1. Aumentar stock fisico
    success: bool = update_stock(product_id, state, quantity, operation='+')
    
    if success:
        # 2. Registrar en historial
        insert_movement(product_id, user_id, "ENTRADA", concept, quantity)
        
    return success

def registrar_salida(
    product_id: int, 
    user_id: int, 
    quantity: int, 
    state: State, 
    concept: str = "Venta"
) -> bool:
    """
    Disminuye el stock físico tras validar reglas de negocio.
    Lanza ValueError si la operación no es permitida.
    """
    # 1. Validar reglas de negocio (ej. no vender si está en cuarentena)
    if concept == "Venta" and state != "Disponible":
        raise ValueError(f"Operación denegada: Solo se puede vender stock 'Disponible' (Estado actual: {state})")

    # 2. Disminuir stock
    success: bool = update_stock(product_id, state, quantity, operation='-')
    
    if not success:
        raise ValueError("Stock insuficiente para realizar la salida")
    
    # 3. Registrar historial
    insert_movement(product_id, user_id, "SALIDA", concept, quantity)
    
    return True