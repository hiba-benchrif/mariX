from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='../static')
    app.config.from_object(config_class)

    # Désactiver le HTTPS strict pour les cookies si on est en développement local avec SQLite
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SESSION_COOKIE_SECURE'] = False

    db.init_app(app)
    login_manager.init_app(app)

    # Importer les blueprints
    from app.auth.routes import auth_bp
    from app.dossiers.routes import dossiers_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dossiers_bp, url_prefix='/dossiers')
    
    from app.chat.routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')

    # Création des tables BDD en local si elles n'existent pas
    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_notifications():
        from app.models import Notification
        from flask_login import current_user
        if current_user.is_authenticated:
            count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return dict(unread_notifications_count=count)
        return dict(unread_notifications_count=0)

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
