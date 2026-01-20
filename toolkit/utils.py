from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)  # No autenticado
        if not current_user.is_admin:
            abort(403)  # No tiene permisos
        return f(*args, **kwargs)
    return decorated_function