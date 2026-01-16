from database.queries import get_user_by_credentials

class Session:
    current_user = None

def login(username, password):
    user = get_user_by_credentials(username, password)
    if user:
        Session.current_user = {"id": user[0], "username": user[1], "role": user[2]}
        return True
    return False

def logout():
    Session.current_user = None

def get_current_user():
    return Session.current_user