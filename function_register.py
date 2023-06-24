import re

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, current_user, login_required
from dataclass import *
from config import *
from mailjet_rest import Client
from itsdangerous import URLSafeTimedSerializer
import bcrypt
from sqlalchemy import func

def inscription_post(session):
    pseudo = request.form['pseudo']
    email = request.form['email']
    email = email.lower()
    password = request.form['password']
    passwordconfirm = request.form['passwordconfirm']
    hash_mail = bcrypt.hashpw(email.encode('utf-8'), BCRYPT_UNIQUE_SALT.encode('utf-8')).decode('utf-8')
    if password != passwordconfirm:
        flash("Les mots de passe ne correspondent pas. Veuillez réessayer.")
        return redirect(url_for('inscription'))
    if session.query(Utilisateurs).filter_by(pseudo=pseudo).first():
        flash("Ce pseudo est déjà utilisé. Veuillez en choisir un autre.")
        return redirect(url_for('inscription'))
    if session.query(Utilisateurs).filter_by(hash_mail=hash_mail).first():
        flash("Cet email est déjà utilisé. Veuillez en choisir un autre.")
        return redirect(url_for('inscription'))
    # Vérifier si la chaîne contient des caractères interdits (pour création de dossier)
    if not is_string_valid(pseudo):
        flash("Le pseudo contient des caractères non autorisés.")
        return redirect(url_for('inscription'))

    hash_mdp = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hash_mdp = hash_mdp.decode('utf-8')
    user = Utilisateurs(pseudo=pseudo, hash_mdp=hash_mdp, hash_mail=hash_mail)
    session.add(user)
    session.commit()

    #email confirmation
    token = generate_confirmation_token(email)
    confirm_url = url_for('confirm_mail', token=token, _external=True)
    mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "matthieus701@gmail.com",
                    "Name": "No-reply Geek-Compagnon"
                },
                "To": [
                    {
                        "Email": email,
                        "Name": pseudo
                    }
                ],
                "Subject": "Confirmation d'inscription Geek-Compagnon",
                "TextPart": "Merci de confirmer votre inscription en cliquant sur le lien suivant : " + confirm_url,
                "HTMLPart": render_template('public/mail.html',  confirm_url=confirm_url),
                "CustomID": "AppGettingStartedTest"
            }
        ]
    }
    try :
        mailjet.send.create(data=data)
    except:
        flash("Une erreur est survenue lors de l'envoi du mail de confirmation. Veuillez réessayer.")
        return redirect(url_for('register'))
    flash("Votre compte a bien été créé. Veuillez cliquer sur le lien de validation dans le mail de confirmation d'inscription afin de pouvoir profiter de nos services.", "success")
    return redirect(url_for('login'))


def inscription_get():
    return render_template('public/register.html')

def is_string_valid(string):
    regex = r"[#\%&\*\+/\\:<>\?\[\]\{\}\|\~\"\$\'\(\),;=]"
    match = re.search(regex, string)
    return match is None

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=SECRET_KEY_SALT)

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(
            token,
            max_age=expiration,
            salt= SECRET_KEY_SALT
        )
    except:
        return False
    return email