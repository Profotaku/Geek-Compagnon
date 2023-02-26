from datetime import timedelta

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import generate_csrf
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from dataclass import *
from config import Config
import pyotp

def get_user_authorizations(user):
    return {"admin": user.admin, "fondateur": user.fondateur, "desactive": user.desactive, "verifie": user.verifie}

def login_web_post(bcrypt, session):
    pseudo = request.form['pseudo']
    password = request.form['password']
    multifact = request.form['multifact']
    remember = bool(request.form.get('remember'))
    user = session.query(Utilisateurs).filter_by(pseudo=pseudo).first()
    if not user or not bcrypt.check_password_hash(user.hash_mdp, password):
        flash('Vos informations de connexion sont incorrectes. Veuillez réessayer.')
        return redirect(url_for('login'))
    elif not user.verifie:
        flash(
            "Ce compte n'a pas encore été activé. Veuillez cliquer sur le lien de validation dans le mail de confirmation d'inscription afin de pouvoir profiter de nos services.")
        return redirect(url_for('login'))
    elif user.desactive:
        flash(
            "Ce compte a été désactivé suite à une demande de l'utilisateur ou pour non respect de nos condition générales d'utilisation. Veuillez contacter l'administrateur du site pour plus d'informations.")
        return redirect(url_for('login'))
    elif user.otp_secret is not None:
        if not pyotp.TOTP(user.otp_secret).verify(multifact):
            flash("Le code de vérification à deux facteurs est incorrect. Veuillez réessayer.")
            return redirect(url_for('login'))
    login_user(user, remember=remember)
    return redirect(url_for('index'))

def login_web_get():
    return render_template('public/login.html')


def login_app_post(bcrypt, session, auth_manager):
    #check if all required fields are present
    if not request.form['pseudo'] or not request.form['password']:
        return jsonify({"success": False, "errormessage": "Veuillez remplir tous les champs."}), 403
    pseudo = request.form['pseudo']
    password = request.form['password']
    multifact = request.form['multifact']
    user = session.query(Utilisateurs).filter_by(pseudo=pseudo).first()
    if not user or not bcrypt.check_password_hash(user.hash_mdp, password):
        return jsonify({"success": False, "errormessage": "Vos informations de connexion sont incorrectes. Veuillez réessayer."}), 403
    elif not user.verifie:
        return jsonify({"success": False, "errormessage": "Ce compte n'a pas encore été activé. Veuillez cliquer sur le lien de validation dans le mail de confirmation d'inscription afin de pouvoir profiter de nos services."}), 403
    elif user.desactive:
        return jsonify({"success": False, "errormessage": "Ce compte a été désactivé suite à une demande de l'utilisateur ou pour non respect de nos condition générales d'utilisation. Veuillez contacter l'administrateur du site pour plus d'informations."}), 403
    elif user.otp_secret is not None:
        if not pyotp.TOTP(user.otp_secret).verify(multifact):
            return jsonify({"success": False, "errormessage": "Le code de vérification à deux facteurs est incorrect. Veuillez réessayer."}), 403
    authorizations = get_user_authorizations(user)
    auth_token = create_access_token(identity=pseudo)
    refresh_token = create_refresh_token(identity=pseudo)
    return jsonify({"success": True, "auth_token": auth_token, "refresh_token": refresh_token }), 200

def login_app_get():
    #return CSRF token i json format
    return jsonify({"csrf_token": generate_csrf()})

