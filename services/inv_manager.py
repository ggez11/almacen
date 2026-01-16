from database.queries import update_stock, insert_movement

def registrar_entrada(product_id, user_id, quantity, state, concept="Compra"):
    # 1. Aumentar stock fisico
    success = update_stock(product_id, state, quantity, operation='+')
    if success:
        # 2. Registrar en historial
        insert_movement(product_id, user_id, "ENTRADA", concept, quantity)
    return success

def registrar_salida(product_id, user_id, quantity, state, concept="Venta"):
    # 1. Validar reglas de negocio (ej. no vender si está en cuarentena)
    if concept == "Venta" and state != "Disponible":
        raise ValueError("Solo se puede vender stock Disponible")

    # 2. Disminuir stock
    success = update_stock(product_id, state, quantity, operation='-')
    if not success:
        raise ValueError("Stock insuficiente")
    
    # 3. Registrar historial
    insert_movement(product_id, user_id, "SALIDA", concept, quantity)
    return True