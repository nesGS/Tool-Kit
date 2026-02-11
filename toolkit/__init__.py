from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página'

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Registrar blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .home import home as home_blueprint
    app.register_blueprint(home_blueprint)
    
    from .station import stations as station_blueprint  # NUEVO
    app.register_blueprint(station_blueprint, url_prefix='/stations')  # NUEVO
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    
    return app