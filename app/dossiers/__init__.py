from flask import Blueprint

dossiers_bp = Blueprint('dossiers', __name__, url_prefix='/dossiers')

from app.dossiers import routes
