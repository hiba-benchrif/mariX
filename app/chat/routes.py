from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.chat import chat_bp
from app.models import MessageInterne, User, Notification, db
from sqlalchemy import or_, and_

@chat_bp.route('/', defaults={'receiver_id': 0})
@chat_bp.route('/<int:receiver_id>')
@login_required
def index(receiver_id):
    # Liste des contacts : tous les utilisateurs sauf soi-même
    contacts = User.query.filter(User.id != current_user.id).all()
    
    receiver = None
    if receiver_id != 0:
        receiver = User.query.get_or_404(receiver_id)
        # Messages privés entre current_user et receiver
        messages = MessageInterne.query.filter(
            or_(
                and_(MessageInterne.sender_id == current_user.id, MessageInterne.receiver_id == receiver_id),
                and_(MessageInterne.sender_id == receiver_id, MessageInterne.receiver_id == current_user.id)
            )
        ).order_by(MessageInterne.created_at.asc()).all()
    else:
        # Messages du groupe global (receiver_id is None)
        messages = MessageInterne.query.filter_by(receiver_id=None).order_by(MessageInterne.created_at.asc()).all()

    # Formater les messages pour le template
    messages_data = []
    for m in messages:
        sender = User.query.get(m.sender_id)
        messages_data.append({
            'id': m.id,
            'sender_id': m.sender_id,
            'sender_name': f"{sender.prenom} {sender.nom}" if sender else "Inconnu",
            'contenu': m.contenu,
            'created_at': m.created_at
        })
        
    return render_template('chat.html', contacts=contacts, current_receiver_id=receiver_id, receiver=receiver, messages=messages_data)

@chat_bp.route('/send/<int:receiver_id>', methods=['POST'])
@login_required
def send_message(receiver_id):
    contenu = request.form.get('contenu')
    if contenu and contenu.strip():
        # receiver_id = 0 signifie Groupe Global (None dans la BDD)
        actual_receiver = None if receiver_id == 0 else receiver_id
        
        msg = MessageInterne(
            sender_id=current_user.id,
            receiver_id=actual_receiver,
            contenu=contenu.strip()
        )
        db.session.add(msg)
        
        # Notification (uniquement pour les messages privés)
        if actual_receiver:
            notif = Notification(
                user_id=actual_receiver,
                message=f"Nouveau message privé de {current_user.prenom} {current_user.nom}.",
                type='info'
            )
            db.session.add(notif)
            
        db.session.commit()
        
    return redirect(url_for('chat.index', receiver_id=receiver_id))
