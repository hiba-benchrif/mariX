from flask import render_template, redirect, url_for, flash, request, session, send_file
from flask_login import login_required, current_user
from app.dossiers import dossiers_bp
from app.dossiers.forms import DossierExportForm, DossierImportForm
from app.models import DossierExport, DossierImport, Historique, Commentaire, Notification, User, db
from app.auth.routes import role_required
import os
import tempfile
from datetime import datetime
from app.utils.ai_parser import extract_data_from_document
from app.utils.excel_generator import generate_employee_report, generate_weekly_report

@dossiers_bp.route('/')
@login_required
def liste_dossiers():
    # Si c'est le responsable, il voit tout
    if current_user.role == 'responsable':
        exports = DossierExport.query.order_by(DossierExport.created_at.desc()).all()
        imports = DossierImport.query.order_by(DossierImport.created_at.desc()).all()
    # Si c'est un employé, il ne voit que ses dossiers
    else:
        exports = DossierExport.query.filter_by(created_by=current_user.id).order_by(DossierExport.created_at.desc()).all()
        imports = DossierImport.query.filter_by(created_by=current_user.id).order_by(DossierImport.created_at.desc()).all()
        
    return render_template('dossiers_liste.html', exports=exports, imports=imports)

@dossiers_bp.route('/export/new', methods=['GET', 'POST'])
@login_required
def new_export():
    form = DossierExportForm()
    
    # Pré-remplissage via IA
    if request.method == 'GET' and 'ia_data' in session:
        ia_data = session.pop('ia_data')
        for key, value in ia_data.items():
            if hasattr(form, key) and value:
                field = getattr(form, key)
                if field.type == 'DateField':
                    try: field.data = datetime.strptime(value, '%Y-%m-%d').date()
                    except: pass
                elif field.type == 'BooleanField':
                    field.data = str(value).lower() == 'true'
                else:
                    field.data = value
    if form.validate_on_submit():
        dossier = DossierExport(
            numero_dossier=form.numero_dossier.data,
            numero_booking=form.numero_booking.data,
            commercial=form.commercial.data,
            client=form.client.data,
            compagnie=form.compagnie.data,
            date_booking=form.date_booking.data,
            date_chargement=form.date_chargement.data,
            date_sequence=form.date_sequence.data,
            etd=form.etd.data,
            pod=form.pod.data,
            eta=form.eta.data,
            nombre_conteneurs=form.nombre_conteneurs.data,
            facturation=form.facturation.data,
            situation=form.situation.data,
            statut=form.statut.data,
            created_by=current_user.id
        )
        db.session.add(dossier)
        db.session.commit()
        
        # Historique
        hist = Historique(dossier_id=dossier.id, dossier_type='export', user_id=current_user.id, action="Création", details="Dossier créé manuellement.")
        db.session.add(hist)
        db.session.commit()
        
        flash('Dossier Export créé avec succès !', 'success')
        return redirect(url_for('dossiers.liste_dossiers'))
        
    return render_template('dossier_export_form.html', form=form, title="Nouveau Dossier Export")

@dossiers_bp.route('/import/new', methods=['GET', 'POST'])
@login_required
def new_import():
    form = DossierImportForm()
    
    # Pré-remplissage via IA
    if request.method == 'GET' and 'ia_data' in session:
        ia_data = session.pop('ia_data')
        for key, value in ia_data.items():
            if hasattr(form, key) and value:
                field = getattr(form, key)
                if field.type == 'DateField':
                    try: field.data = datetime.strptime(value, '%Y-%m-%d').date()
                    except: pass
                else:
                    field.data = value
    if form.validate_on_submit():
        dossier = DossierImport(
            numero_dossier=form.numero_dossier.data,
            commercial=form.commercial.data,
            exploitant=form.exploitant.data,
            type_conteneur=form.type_conteneur.data,
            fournisseur=form.fournisseur.data,
            client=form.client.data,
            mbl=form.mbl.data,
            incoterm=form.incoterm.data,
            agent=form.agent.data,
            compagnie=form.compagnie.data,
            pol=form.pol.data,
            pod=form.pod.data,
            etd=form.etd.data,
            eta=form.eta.data,
            achat=form.achat.data,
            vente=form.vente.data,
            pays=form.pays.data,
            situation=form.situation.data,
            statut=form.statut.data,
            created_by=current_user.id
        )
        db.session.add(dossier)
        db.session.commit()
        
        hist = Historique(dossier_id=dossier.id, dossier_type='import', user_id=current_user.id, action="Création", details="Dossier créé manuellement.")
        db.session.add(hist)
        db.session.commit()
        
        flash('Dossier Import créé avec succès !', 'success')
        return redirect(url_for('dossiers.liste_dossiers'))
        
    return render_template('dossier_import_form.html', form=form, title="Nouveau Dossier Import")

@dossiers_bp.route('/export/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_export(id):
    dossier = DossierExport.query.get_or_404(id)
    # Vérifier les permissions
    if current_user.role != 'responsable' and dossier.created_by != current_user.id:
        flash("Vous n'avez pas l'autorisation de modifier ce dossier.", "danger")
        return redirect(url_for('dossiers.liste_dossiers'))
        
    form = DossierExportForm(obj=dossier)
    if form.validate_on_submit():
        form.populate_obj(dossier)
        db.session.commit()
        
        hist = Historique(dossier_id=dossier.id, dossier_type='export', user_id=current_user.id, action="Modification", details="Dossier mis à jour.")
        db.session.add(hist)
        db.session.commit()
        
        flash('Dossier Export modifié avec succès !', 'success')
        return redirect(url_for('dossiers.liste_dossiers'))
        
    comments_data = []
    commentaires = Commentaire.query.filter_by(dossier_id=id, dossier_type='export').order_by(Commentaire.created_at.asc()).all()
    for c in commentaires:
        u = User.query.get(c.user_id)
        comments_data.append({'texte': c.texte, 'date': c.created_at, 'auteur': f"{u.prenom} {u.nom}" if u else "Inconnu", 'role': u.role if u else ""})
        
    return render_template('dossier_export_form.html', form=form, title=f"Modifier Dossier Export N°{dossier.numero_dossier}", commentaires=comments_data, dossier_id=id, dossier_type='export')

@dossiers_bp.route('/import/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_import(id):
    dossier = DossierImport.query.get_or_404(id)
    if current_user.role != 'responsable' and dossier.created_by != current_user.id:
        flash("Vous n'avez pas l'autorisation de modifier ce dossier.", "danger")
        return redirect(url_for('dossiers.liste_dossiers'))
        
    form = DossierImportForm(obj=dossier)
    if form.validate_on_submit():
        form.populate_obj(dossier)
        db.session.commit()
        
        hist = Historique(dossier_id=dossier.id, dossier_type='import', user_id=current_user.id, action="Modification", details="Dossier mis à jour.")
        db.session.add(hist)
        db.session.commit()
        
        flash('Dossier Import modifié avec succès !', 'success')
        return redirect(url_for('dossiers.liste_dossiers'))
        
    comments_data = []
    commentaires = Commentaire.query.filter_by(dossier_id=id, dossier_type='import').order_by(Commentaire.created_at.asc()).all()
    for c in commentaires:
        u = User.query.get(c.user_id)
        comments_data.append({'texte': c.texte, 'date': c.created_at, 'auteur': f"{u.prenom} {u.nom}" if u else "Inconnu", 'role': u.role if u else ""})
        
    return render_template('dossier_import_form.html', form=form, title=f"Modifier Dossier Import N°{dossier.numero_dossier}", commentaires=comments_data, dossier_id=id, dossier_type='import')

@dossiers_bp.route('/comment/<type>/<int:id>', methods=['POST'])
@login_required
def add_comment(type, id):
    texte = request.form.get('texte')
    if texte and texte.strip():
        comment = Commentaire(dossier_id=id, dossier_type=type, user_id=current_user.id, texte=texte.strip())
        db.session.add(comment)
        
        # Obtenir le dossier pour trouver son créateur
        dossier = DossierExport.query.get(id) if type == 'export' else DossierImport.query.get(id)
        
        if dossier:
            # Si un employé commente -> notifier tous les responsables
            if current_user.role == 'employe':
                responsables = User.query.filter_by(role='responsable').all()
                for resp in responsables:
                    notif = Notification(
                        user_id=resp.id,
                        message=f"Nouveau commentaire de {current_user.prenom} sur le dossier {type.capitalize()} N°{dossier.numero_dossier}.",
                        type='info'
                    )
                    db.session.add(notif)
            # Si un responsable commente -> notifier le créateur du dossier
            elif current_user.role == 'responsable':
                # S'assurer que le responsable ne se notifie pas lui-même s'il a créé le dossier
                if current_user.id != dossier.created_by:
                    notif = Notification(
                        user_id=dossier.created_by,
                        message=f"Nouveau commentaire de {current_user.prenom} (Responsable) sur votre dossier {type.capitalize()} N°{dossier.numero_dossier}.",
                        type='alerte'
                    )
                    db.session.add(notif)
                
        db.session.commit()
        flash('Commentaire ajouté.', 'success')
    
    if type == 'export':
        return redirect(url_for('dossiers.edit_export', id=id))
    else:
        return redirect(url_for('dossiers.edit_import', id=id))

@dossiers_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    # Marquer toutes les notifications comme lues
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)

@dossiers_bp.route('/upload_ia/<type>', methods=['GET', 'POST'])
@login_required
def upload_ia(type):
    if request.method == 'POST':
        if 'document' not in request.files:
            flash("Aucun fichier n'a été fourni.", "danger")
            return redirect(request.url)
        file = request.files['document']
        if file.filename == '':
            flash("Aucun fichier sélectionné.", "danger")
            return redirect(request.url)
            
        # Sauvegarde temporaire
        ext = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
            file.save(temp.name)
            temp_path = temp.name
            
        # Extraction IA
        ia_data = extract_data_from_document(temp_path, type)
        
        # Nettoyage
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if ia_data:
            session['ia_data'] = ia_data
            flash("Document analysé avec succès par l'IA. Veuillez vérifier les données pré-remplies.", "success")
        else:
            flash("L'IA n'a pas pu extraire de données fiables. Veuillez remplir le formulaire manuellement.", "warning")
            
        if type == 'export':
            return redirect(url_for('dossiers.new_export'))
        else:
            return redirect(url_for('dossiers.new_import'))
            
    return render_template('upload_ia.html', type=type)

@dossiers_bp.route('/rapport_employe')
@login_required
def rapport_employe():
    filepath = generate_employee_report(current_user.id)
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

@dossiers_bp.route('/rapport_hebdomadaire')
@login_required
def rapport_hebdomadaire():
    if current_user.role != 'responsable':
        flash("Accès non autorisé.", "danger")
        return redirect(url_for('auth.dashboard'))
    filepath = generate_weekly_report()
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
