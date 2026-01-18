from typing import Literal, Optional, NoReturn
from database.queries import update_stock, insert_movement, get_product_stock

# Definición de Tipos
State = Literal["Disponible", "Cuarentena", "Dañado"]
MovementType = Literal["ENTRADA", "SALIDA"]

class InventoryManager:
    """
    Controlador de lógica de negocio para operaciones de inventario.
    Centraliza validaciones y transacciones de stock.
    """

    def registrar_entrada(
        self, 
        product_id: int, 
        user_id: int, 
        quantity: int, 
        state: State, 
        concept: str = "Compra"
    ) -> bool:
        """
        Aumenta el stock físico y registra el movimiento.
        """
        if quantity <= 0:
            raise ValueError("La cantidad de entrada debe ser mayor a 0.")

        # 1. Aumentar stock físico
        success: bool = update_stock(product_id, state, quantity, operation='+')
        
        if success:
            # 2. Registrar historial
            self._log_movement(product_id, user_id, "ENTRADA", concept, quantity)
            
        return success

    def registrar_salida(
        self, 
        product_id: int, 
        user_id: int, 
        quantity: int, 
        state: State, 
        concept: str = "Venta"
    ) -> bool:
        """
        Disminuye stock validando reglas de negocio.
        """
        if quantity <= 0:
            raise ValueError("La cantidad de salida debe ser mayor a 0.")

        # 1. Validaciones de Negocio (Método privado)
        self._validar_reglas_salida(state, concept)
        
        # 2. Verificar si hay stock suficiente antes de intentar update (Opcional pero recomendado)
        current_stock: int = get_product_stock(product_id, state)
        if current_stock < quantity:
            raise ValueError(f"Stock insuficiente. Disponible: {current_stock}, Solicitado: {quantity}")

        # 3. Disminuir stock
        success: bool = update_stock(product_id, state, quantity, operation='-')
        
        if not success:
            raise ValueError("Error al actualizar la base de datos.")
        
        # 4. Registrar historial
        self._log_movement(product_id, user_id, "SALIDA", concept, quantity)
        
        return True

    def transferir_stock(
        self,
        product_id: int,
        user_id: int,
        qty: int,
        origen: State,
        destino: State
    ) -> bool:
        """
        Mueve stock de un estado a otro (Ej: De 'Cuarentena' a 'Disponible').
        Esto es una operación compuesta (Salida + Entrada interna).
        """
        # Usamos una transacción atómica lógica
        try:
            # 1. Sacar del origen (Concepto interno)
            self.registrar_salida(product_id, user_id, qty, origen, concept="Transferencia Salida")
            
            # 2. Meter al destino
            self.registrar_entrada(product_id, user_id, qty, destino, concept="Transferencia Entrada")
            return True
        except ValueError as e:
            # Aquí idealmente harías rollback si la DB lo soporta, 
            # pero por ahora relanzamos el error para la UI.
            raise e

    # --- MÉTODOS PRIVADOS (Helpers internos) ---

    def _validar_reglas_salida(self, state: State, concept: str) -> None:
        """Centraliza las reglas de qué se puede vender y qué no."""
        # Regla 1: Solo se vende lo disponible
        if concept in ["Venta", "Pedido Web"] and state != "Disponible":
            raise ValueError(f"No se puede vender productos en estado '{state}'.")
        
        # Regla 2: No se puede sacar nada que esté Dañado para venta (solo para Merma)
        if state == "Dañado" and concept != "Merma":
            raise ValueError("El stock dañado solo puede salir por concepto de Merma.")

    def _log_movement(
        self, 
        prod_id: int, 
        user_id: int, 
        tipo: MovementType, 
        concept: str, 
        qty: int
    ) -> None:
        """Wrapper para la inserción en DB."""
        insert_movement(prod_id, user_id, tipo, concept, qty)