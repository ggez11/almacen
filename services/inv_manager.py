from typing import Literal, Optional, Dict, Any, List
from database.queries import ajustar_stock, get_product_stock
from services.auth_service import get_current_user

# Definición de Tipos actualizados
MovementType = Literal["IN", "OUT"]
RazonType = Literal["venta", "ajuste manual", "dañado", "vencido", "robo", "uso interno", 
                    "transferencia", "recepcion", "compra", "merma", "devolucion"]

class InventoryManager:
    """
    Controlador de lógica de negocio para operaciones de inventario.
    Adaptado a la nueva estructura de base de datos.
    """

    def __init__(self):
        """Inicializa el manager con el usuario actual."""
        self.current_user = get_current_user()

    def registrar_entrada(
        self, 
        product_id: int, 
        quantity: int, 
        razon: RazonType = "recepcion",
        ubicacion_id: Optional[int] = None,
        razon_detalle: Optional[str] = None,
        observaciones: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Aumenta el stock físico y registra el movimiento.
        
        Args:
            product_id: ID del producto
            quantity: Cantidad a añadir
            razon: Razón de la entrada
            ubicacion_id: ID de la ubicación (opcional, se usará la primera disponible si no se especifica)
            razon_detalle: Detalle adicional de la razón
            observaciones: Observaciones del movimiento
            user_id: ID del usuario (opcional, se usará el usuario actual si no se especifica)
            
        Returns:
            bool: True si la operación fue exitosa
        """
        if quantity <= 0:
            raise ValueError("La cantidad de entrada debe ser mayor a 0.")

        # Obtener usuario
        if not user_id:
            if not self.current_user:
                raise ValueError("No hay usuario autenticado")
            user_id = self.current_user.id

        # Obtener ubicación si no se especifica
        if not ubicacion_id:
            ubicacion_id = self._obtener_ubicacion_predeterminada()

        # Registrar el movimiento de entrada
        success = ajustar_stock(
            producto_id=product_id,
            ubicacion_id=ubicacion_id,
            cantidad=quantity,
            tipo='IN',
            razon=razon,
            razon_detalle=razon_detalle,
            usuario_id=user_id,
            observaciones=observaciones
        )
        
        if not success:
            raise ValueError("Error al registrar la entrada en la base de datos.")
        
        return True

    def registrar_salida(
        self, 
        product_id: int, 
        quantity: int, 
        razon: RazonType = "venta",
        ubicacion_id: Optional[int] = None,
        razon_detalle: Optional[str] = None,
        observaciones: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Disminuye stock validando reglas de negocio.
        
        Args:
            product_id: ID del producto
            quantity: Cantidad a retirar
            razon: Razón de la salida
            ubicacion_id: ID de la ubicación
            razon_detalle: Detalle adicional de la razón
            observaciones: Observaciones del movimiento
            user_id: ID del usuario
            
        Returns:
            bool: True si la operación fue exitosa
        """
        if quantity <= 0:
            raise ValueError("La cantidad de salida debe ser mayor a 0.")

        # Validar reglas de negocio
        self._validar_reglas_salida(razon, quantity)

        # Obtener usuario
        if not user_id:
            if not self.current_user:
                raise ValueError("No hay usuario autenticado")
            user_id = self.current_user.id

        # Obtener ubicación si no se especifica
        if not ubicacion_id:
            ubicacion_id = self._obtener_ubicacion_predeterminada()

        # Verificar stock disponible
        if ubicacion_id:
            stock_actual = get_product_stock(product_id, ubicacion_id)
        else:
            stock_actual = get_product_stock(product_id)
            
        if stock_actual < quantity:
            raise ValueError(f"Stock insuficiente. Disponible: {stock_actual}, Solicitado: {quantity}")

        # Registrar el movimiento de salida
        success = ajustar_stock(
            producto_id=product_id,
            ubicacion_id=ubicacion_id,
            cantidad=quantity,
            tipo='OUT',
            razon=razon,
            razon_detalle=razon_detalle,
            usuario_id=user_id,
            observaciones=observaciones
        )
        
        if not success:
            raise ValueError("Error al registrar la salida en la base de datos.")
        
        return True

    def ajuste_manual(
        self,
        product_id: int,
        cantidad_nueva: int,
        ubicacion_id: Optional[int] = None,
        razon_detalle: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Ajuste manual de stock a un valor específico.
        Calcula automáticamente la diferencia y la registra como entrada o salida.
        """
        if not ubicacion_id:
            ubicacion_id = self._obtener_ubicacion_predeterminada()

        # Obtener stock actual
        if ubicacion_id:
            stock_actual = get_product_stock(product_id, ubicacion_id)
        else:
            stock_actual = get_product_stock(product_id)

        # Calcular diferencia
        diferencia = cantidad_nueva - stock_actual
        
        if diferencia == 0:
            return True  # No hay cambio
        
        if diferencia > 0:
            # Es una entrada
            return self.registrar_entrada(
                product_id=product_id,
                quantity=diferencia,
                razon="ajuste manual",
                ubicacion_id=ubicacion_id,
                razon_detalle=razon_detalle or f"Ajuste manual: de {stock_actual} a {cantidad_nueva}",
                user_id=user_id
            )
        else:
            # Es una salida (valor absoluto)
            return self.registrar_salida(
                product_id=product_id,
                quantity=abs(diferencia),
                razon="ajuste manual",
                ubicacion_id=ubicacion_id,
                razon_detalle=razon_detalle or f"Ajuste manual: de {stock_actual} a {cantidad_nueva}",
                user_id=user_id
            )

    def registrar_merma(
        self,
        product_id: int,
        cantidad: int,
        tipo_merma: RazonType,  # 'dañado', 'vencido', 'robo', 'uso interno'
        ubicacion_id: Optional[int] = None,
        detalle: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Registra una merma (pérdida de inventario).
        """
        if tipo_merma not in ['dañado', 'vencido', 'robo', 'uso interno']:
            raise ValueError(f"Tipo de merma no válido: {tipo_merma}")

        return self.registrar_salida(
            product_id=product_id,
            quantity=cantidad,
            razon=tipo_merma,
            ubicacion_id=ubicacion_id,
            razon_detalle=detalle,
            observaciones=f"Merma registrada: {tipo_merma}",
            user_id=user_id
        )

    def transferir_entre_ubicaciones(
        self,
        product_id: int,
        cantidad: int,
        ubicacion_origen_id: int,
        ubicacion_destino_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Transfiere stock entre ubicaciones.
        """
        try:
            # Sacar de la ubicación origen
            self.registrar_salida(
                product_id=product_id,
                quantity=cantidad,
                razon="transferencia",
                ubicacion_id=ubicacion_origen_id,
                razon_detalle=f"Transferencia a ubicación {ubicacion_destino_id}",
                user_id=user_id
            )
            
            # Meter en la ubicación destino
            self.registrar_entrada(
                product_id=product_id,
                quantity=cantidad,
                razon="transferencia",
                ubicacion_id=ubicacion_destino_id,
                razon_detalle=f"Transferencia desde ubicación {ubicacion_origen_id}",
                user_id=user_id
            )
            
            return True
        except ValueError as e:
            # En un sistema más complejo, aquí se haría rollback
            raise ValueError(f"Error en transferencia: {e}")

    # --- MÉTODOS PRIVADOS (Helpers internos) ---

    def _validar_reglas_salida(self, razon: RazonType, cantidad: int) -> None:
        """
        Centraliza las reglas de qué se puede vender y qué no.
        """
        # Regla 1: Validar cantidad
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        
        # Regla 2: Validaciones específicas por razón
        if razon == "venta":
            # Validaciones adicionales para ventas
            pass
        
        elif razon in ["dañado", "vencido", "robo", "uso interno"]:
            # Validaciones para mermas
            pass

    def _obtener_ubicacion_predeterminada(self) -> int:
        """
        Obtiene la primera ubicación disponible.
        En un sistema real, esto podría basarse en preferencias o configuraciones.
        """
        from database.queries import obtener_ubicaciones
        
        ubicaciones = obtener_ubicaciones()
        if not ubicaciones:
            raise ValueError("No hay ubicaciones disponibles en el sistema")
        
        # Retornar la primera ubicación disponible
        return ubicaciones[0][0]

    # --- MÉTODOS DE COMPATIBILIDAD CON CÓDIGO ANTIGUO ---
    
    def registrar_entrada_legacy(
        self, 
        product_id: int, 
        user_id: int, 
        quantity: int, 
        concept: str = "Compra"
    ) -> bool:
        """
        Método de compatibilidad con código antiguo.
        """
        # Mapear conceptos a razones
        razon_map = {
            "Compra": "compra",
            "Transferencia Entrada": "transferencia",
            "Devolucion": "devolucion"
        }
        
        return self.registrar_entrada(
            product_id=product_id,
            quantity=quantity,
            razon=razon_map.get(concept, "recepcion"),
            razon_detalle=f"Concepto: {concept}",
            user_id=user_id
        )

    def registrar_salida_legacy(
        self, 
        product_id: int, 
        user_id: int, 
        quantity: int, 
        concept: str = "Venta"
    ) -> bool:
        """
        Método de compatibilidad con código antiguo.
        """
        # Mapear conceptos a razones
        razon_map = {
            "Venta": "venta",
            "Merma": "merma",
            "Transferencia Salida": "transferencia"
        }
        
        return self.registrar_salida(
            product_id=product_id,
            quantity=quantity,
            razon=razon_map.get(concept, "ajuste manual"),
            razon_detalle=f"Concepto: {concept}",
            user_id=user_id
        )