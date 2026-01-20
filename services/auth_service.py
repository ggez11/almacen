# services/auth_service.py - VERSIÓN ACTUALIZADA Y LIMPIA
from dataclasses import dataclass
from typing import Optional, Dict
from database.queries import get_user_by_credentials

@dataclass
class User:
    """Clase para representar la estructura de un usuario en sesión."""
    id: int
    username: str
    role: str  # 'Administrador', 'Almacenero', 'Consultor'
    
    def has_permission(self, permission: str) -> bool:
        """
        Verifica si el usuario tiene un permiso específico basado en su rol.
        
        Permisos disponibles:
        - 'inventario_view': Ver inventario
        - 'inventario_edit': Editar inventario (ajustar stock)
        - 'movimientos_view': Ver movimientos
        - 'movimientos_edit': Crear movimientos
        - 'ventas_view': Ver ventas
        - 'ventas_edit': Crear ventas
        - 'configuracion': Configuración del sistema
        - 'usuarios': Gestión de usuarios
        """
        permisos_por_rol = {
            'Administrador': [
                'inventario_view', 'inventario_edit',
                'movimientos_view', 'movimientos_edit',
                'ventas_view', 'ventas_edit',
                'configuracion', 'usuarios'
            ],
            'Almacenero': [
                'inventario_view', 'inventario_edit',  # Solo ajustar stock en inventario y salidas
                'movimientos_view',
                'ventas_view'
            ],
            'Consultor': [
                'movimientos_view',  # Acceso completo a movimientos
                'inventario_view',   # Solo lectura en inventario
                'ventas_view'        # Solo lectura en ventas
            ]
        }
        
        return permission in permisos_por_rol.get(self.role, [])

class Session:
    """Clase singleton para manejar la sesión del usuario."""
    current_user: Optional[User] = None
    
    @classmethod
    def get_instance(cls):
        """Retorna la instancia única de la sesión."""
        return cls
    
    @classmethod
    def is_authenticated(cls) -> bool:
        """Verifica si hay un usuario autenticado."""
        return cls.current_user is not None
    
    @classmethod
    def get_role(cls) -> str:
        """Retorna el rol del usuario actual o 'Invitado' si no hay sesión."""
        if cls.current_user:
            return cls.current_user.role
        return 'Invitado'

def login(username: str, password: str) -> bool:
    """
    Verifica credenciales y establece la sesión usando la dataclass User.
    """
    user_data: Optional[tuple] = get_user_by_credentials(username, password)
    
    if user_data:
        # user_data[0] = id, user_data[1] = usuario, user_data[2] = rol
        Session.current_user = User(
            id=user_data[0], 
            username=user_data[1], 
            role=user_data[2]
        )
        return True
    return False

def logout() -> None:
    """Limpia la sesión actual."""
    Session.current_user = None

def get_current_user() -> Optional[User]:
    """Retorna la instancia de User logueado o None."""
    return Session.current_user

def check_permission(permission: str) -> bool:
    """
    Verifica si el usuario actual tiene un permiso específico.
    
    Args:
        permission: El permiso a verificar
        
    Returns:
        bool: True si tiene permiso, False en caso contrario
    """
    user = get_current_user()
    if not user:
        return False
    return user.has_permission(permission)

def get_user_info() -> Dict[str, any]:
    """
    Retorna información del usuario actual en formato diccionario.
    
    Returns:
        Dict con información del usuario o diccionario vacío si no hay sesión
    """
    user = get_current_user()
    if user:
        return {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'is_admin': user.role == 'Administrador',
            'is_almacenero': user.role == 'Almacenero',
            'is_consultor': user.role == 'Consultor'
        }
    return {}