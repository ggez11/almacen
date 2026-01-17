from dataclasses import dataclass
from typing import Optional
from database.queries import get_user_by_credentials

@dataclass
class User:
    """Clase para representar la estructura de un usuario en sesión."""
    id: int
    username: str
    role: str

class Session:
    current_user: Optional[User] = None

def login(username: str, password: str) -> bool:
    """
    Verifica credenciales y establece la sesión usando la dataclass User.
    """
    user_data: Optional[tuple] = get_user_by_credentials(username, password)
    
    if user_data:
        
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