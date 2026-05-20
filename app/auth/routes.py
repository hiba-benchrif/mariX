from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import auth_bp
from app.auth.forms import LoginForm
from app.models import User
import bcrypt
from functools import wraps
from flask import abort

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    # Si des utilisateurs existent déjà, interdire l'accès
    if User.query.first():
        flash('Le compte responsable existe déjà.', 'warning')
        return redirect(url_for('auth.login'))
    
    from app.auth.forms import SetupForm
    form = SetupForm()
    
    if form.validate_on_submit():
        from app import db
        hashed_pw = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        responsable = User(
            nom=form.nom.data,
            prenom=form.prenom.data,
            email=form.email.data,
            password_hash=hashed_pw,
            role='responsable',
            affectation='les_deux',
            is_active=True
        )
        db.session.add(responsable)
        db.session.commit()
        flash('Votre compte Responsable a été créé avec succès. Connectez-vous !', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('setup.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si aucun utilisateur n'existe, rediriger vers la page de configuration initiale
    if not User.query.first():
        return redirect(url_for('auth.setup'))
    
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.checkpw(form.password.data.encode('utf-8'), user.password_hash.encode('utf-8')):
            login_user(user)
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')
            
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    from app.auth.forms import EditProfileForm
    form = EditProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.nom = form.nom.data
        current_user.prenom = form.prenom.data
        
        if form.password.data:
            hashed_pw = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            current_user.password_hash = hashed_pw
            
        from app import db
        db.session.commit()
        flash('Votre profil a été mis à jour avec succès.', 'success')
        return redirect(url_for('auth.profil'))
        
    return render_template('profil.html', form=form)

from app.models import DossierExport, DossierImport, Notification, User, db
from datetime import datetime, timedelta

@auth_bp.route('/')
@auth_bp.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    if current_user.role == 'responsable':
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        
        imports_semaine = DossierImport.query.filter(DossierImport.created_at >= start_of_week).count()
        exports_semaine = DossierExport.query.filter(DossierExport.created_at >= start_of_week).count()
        total_semaine = imports_semaine + exports_semaine
        
        total_imports = DossierImport.query.count()
        total_exports = DossierExport.query.count()
        
        anomalies_ia = 0 # À implémenter avec un flag dans les modèles si nécessaire
        en_retard = 0 
        employes_actifs = User.query.filter_by(role='employe', is_active=True).count()
        
        recent_exports = DossierExport.query.order_by(DossierExport.created_at.desc()).limit(5).all()
        recent_imports = DossierImport.query.order_by(DossierImport.created_at.desc()).limit(5).all()
        
        tous_recents = []
        for d in recent_exports:
            user = User.query.get(d.created_by)
            tous_recents.append({'dossier': d, 'type': 'Export', 'date': d.created_at, 'employe': f"{user.prenom} {user.nom}" if user else "Inconnu"})
        for d in recent_imports:
            user = User.query.get(d.created_by)
            tous_recents.append({'dossier': d, 'type': 'Import', 'date': d.created_at, 'employe': f"{user.prenom} {user.nom}" if user else "Inconnu"})
            
        tous_recents.sort(key=lambda x: x['date'], reverse=True)
        tous_recents = tous_recents[:5]

        return render_template('dashboard_responsable.html',
            total_semaine=total_semaine, total_imports=total_imports, total_exports=total_exports,
            anomalies_ia=anomalies_ia, en_retard=en_retard, employes_actifs=employes_actifs,
            recents=tous_recents)
    else:
        my_exports = DossierExport.query.filter_by(created_by=current_user.id).all()
        my_imports = DossierImport.query.filter_by(created_by=current_user.id).all()
        all_my = my_exports + my_imports
        
        en_cours = sum(1 for d in all_my if getattr(d, 'statut', '') == 'En cours')
        clotures = sum(1 for d in all_my if getattr(d, 'statut', '') == 'Clôturé')
        en_attente = sum(1 for d in all_my if getattr(d, 'statut', '') not in ['En cours', 'Clôturé'])
        
        alertes = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
        my_recents = []
        for d in sorted(my_exports, key=lambda x: getattr(x, 'created_at', datetime.min), reverse=True)[:5]:
            my_recents.append({'dossier': d, 'type': 'Export', 'date': getattr(d, 'created_at', datetime.now())})
        for d in sorted(my_imports, key=lambda x: getattr(x, 'created_at', datetime.min), reverse=True)[:5]:
            my_recents.append({'dossier': d, 'type': 'Import', 'date': getattr(d, 'created_at', datetime.now())})
            
        my_recents.sort(key=lambda x: x['date'], reverse=True)
        my_recents = my_recents[:5]

        return render_template('dashboard_employe.html',
            en_cours=en_cours, en_attente=en_attente, clotures=clotures, alertes=alertes,
            recents=my_recents)

@auth_bp.route('/employes', methods=['GET', 'POST'])
@login_required
@role_required('responsable')
def employes():
    from app.auth.forms import AddEmployeeForm
    form = AddEmployeeForm()
    
    if form.validate_on_submit():
        # Vérifier si l'email existe déjà
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Cet email est déjà utilisé par un autre compte.', 'danger')
        else:
            # Hachage du mot de passe
            hashed_pw = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Création de l'utilisateur
            new_user = User(
                nom=form.nom.data,
                prenom=form.prenom.data,
                email=form.email.data,
                password_hash=hashed_pw,
                role='employe',
                affectation=form.affectation.data,
                is_active=True
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash(f"L'employé {new_user.prenom} {new_user.nom} a été créé avec succès.", 'success')
            return redirect(url_for('auth.employes'))
            
    # Liste de tous les employés (exclure le responsable actuel si besoin, ou juste tous les 'employe')
    liste_employes = User.query.filter_by(role='employe').order_by(User.created_at.desc()).all()
    
    return render_template('employes_liste.html', form=form, employes=liste_employes)

@auth_bp.route('/init-db')
def init_db():
    from app import db
    if not User.query.first():
        hashed_pw = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(nom='Admin', prenom='System', email='admin@marix.com', password_hash=hashed_pw, role='responsable', affectation='les_deux')
        hashed_pw2 = bcrypt.hashpw('employe'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        employe = User(nom='Employé', prenom='Test', email='employe@marix.com', password_hash=hashed_pw2, role='employe', affectation='import')
        db.session.add(admin)
        db.session.add(employe)
        db.session.commit()
        return "Comptes de test créés : admin@marix.com / admin | employe@marix.com / employe"
    return "Base de données déjà initialisée."
