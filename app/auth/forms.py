from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message="L'email est requis."), Email(message="Email invalide.")])
    password = PasswordField('Mot de passe', validators=[DataRequired(message="Le mot de passe est requis.")])
    submit = SubmitField('Se connecter')

class AddEmployeeForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired(message="Le nom est requis.")])
    prenom = StringField('Prénom', validators=[DataRequired(message="Le prénom est requis.")])
    email = StringField('Email', validators=[DataRequired(message="L'email est requis."), Email(message="Email invalide.")])
    password = PasswordField('Mot de passe provisoire', validators=[DataRequired(message="Le mot de passe est requis.")])
    affectation = SelectField('Affectation', choices=[('import', 'Import'), ('export', 'Export'), ('les_deux', 'Les deux')], validators=[DataRequired()])
    submit = SubmitField('Créer le compte Employé')

class EditProfileForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired(message="Le nom est requis.")])
    prenom = StringField('Prénom', validators=[DataRequired(message="Le prénom est requis.")])
    password = PasswordField('Nouveau mot de passe (laisser vide pour ne pas changer)')
    submit = SubmitField('Mettre à jour le profil')
