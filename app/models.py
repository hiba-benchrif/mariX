from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20)) # 'employe' ou 'responsable'
    affectation = db.Column(db.String(20)) # 'import', 'export', 'les_deux'
    is_active = db.Column(db.Boolean, default=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_online(self):
        """Un utilisateur est considéré en ligne s'il a été actif dans les 5 dernières minutes."""
        if not self.last_activity:
            return False
        from datetime import timedelta
        return (datetime.utcnow() - self.last_activity) < timedelta(minutes=5)

class DossierExport(db.Model):
    __tablename__ = 'dossiers_export'
    id = db.Column(db.Integer, primary_key=True)
    numero_dossier = db.Column(db.String(50), nullable=False)
    numero_booking = db.Column(db.String(50))
    commercial = db.Column(db.String(100))
    client = db.Column(db.String(100))
    compagnie = db.Column(db.String(100))
    date_booking = db.Column(db.Date)
    date_chargement = db.Column(db.Date)
    date_sequence = db.Column(db.Date)
    etd = db.Column(db.Date)
    pod = db.Column(db.String(100))
    eta = db.Column(db.Date)
    nombre_conteneurs = db.Column(db.String(50))
    facturation = db.Column(db.Boolean, default=False)
    situation = db.Column(db.Text)
    statut = db.Column(db.String(50))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DossierImport(db.Model):
    __tablename__ = 'dossiers_import'
    id = db.Column(db.Integer, primary_key=True)
    numero_dossier = db.Column(db.String(50))
    commercial = db.Column(db.String(100))
    exploitant = db.Column(db.String(100))
    type_conteneur = db.Column(db.String(50))
    fournisseur = db.Column(db.String(100))
    client = db.Column(db.String(100))
    mbl = db.Column(db.String(100))
    incoterm = db.Column(db.String(50))
    agent = db.Column(db.String(100))
    compagnie = db.Column(db.String(100))
    pol = db.Column(db.String(100))
    pod = db.Column(db.String(100))
    etd = db.Column(db.Date)
    eta = db.Column(db.Date)
    achat = db.Column(db.Numeric(10, 2))
    vente = db.Column(db.Numeric(10, 2))
    pays = db.Column(db.String(100))
    situation = db.Column(db.Text)
    statut = db.Column(db.String(50))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    dossier_id = db.Column(db.Integer)
    dossier_type = db.Column(db.String(10)) # 'import' ou 'export'
    nom_fichier = db.Column(db.String(255))
    url_cloudinary = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Commentaire(db.Model):
    __tablename__ = 'commentaires'
    id = db.Column(db.Integer, primary_key=True)
    dossier_id = db.Column(db.Integer, nullable=False)
    dossier_type = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    texte = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Historique(db.Model):
    __tablename__ = 'historique'
    id = db.Column(db.Integer, primary_key=True)
    dossier_id = db.Column(db.Integer)
    dossier_type = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100))
    details = db.Column(db.Text)
    date_action = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text)
    type = db.Column(db.String(50)) # 'alerte', 'info', 'rapport'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MessageInterne(db.Model):
    __tablename__ = 'messages_internes'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Null = Message de groupe (Canal Général)
    contenu = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
