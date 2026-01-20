from toolkit import create_app, db
from toolkit.models import User

app = create_app()

with app.app_context():
    # Verificar si ya existe un admin
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("Ya existe un usuario admin")
    else:
        # Crear el primer admin
        admin = User(
            username='admin',
            email='admin@tuempresa.com',
            is_admin=True
        )
        admin.set_password('admin123')  # CÁMBIALA DESPUÉS
        
        db.session.add(admin)
        db.session.commit()
        
        print("Usuario admin creado exitosamente")
        print("Username: admin")
        print("Password: admin123")
        print("¡CAMBIA LA CONTRASEÑA DESPUÉS DE INICIAR SESIÓN!")