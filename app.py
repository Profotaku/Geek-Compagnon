# -*- coding: utf-8 -*-
import time
import uuid

import flask
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_file, make_response, g
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from cache import cache
import sqlalchemy as sa  # ORM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm, or_, and_, select, join, outerjoin, text, func, desc
from sqlalchemy_searchable import make_searchable, search
from flask_wtf.csrf import CSRFProtect # CSRF protection
from flask_mailman import Mail  # API for sending emails
from flask_cors import CORS  # prevent CORS attacks
import bcrypt
from uuid import uuid4
from PIL import Image
from flask_login import LoginManager, AnonymousUserMixin  # user session management
from huey import RedisHuey, crontab  # task queue
from flask_ipban import IpBan  # IP ban
from sqlalchemy import literal_column
from sqlalchemy.sql.operators import op
import sqlalchemy.sql.functions
from flask_assets import Bundle, Environment
from flask_login import login_user, logout_user, current_user, login_required
from flask_pyjwt import AuthManager, require_token, current_token
from flask_talisman import Talisman # security headers
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
	verify_jwt_in_request
from flask_session import Session
from flask_dropzone import Dropzone
from flask_squeeze import Squeeze
import io
import os

import function_search
from config import *
import config
from dataclass import *
import recommandations
import function_login
import function_register
import function_addfiche
import function_bibliotheque
import function_collection
import function_mybibliotheque
import function_mycollection
import function_produit_culturel
import function_projet_media
import function_projet_transmedia
import function_user_stats
import function_user_settings
import pyotp
import pyqrcode
from apputils import make_cache_key
from sqlalchemy.orm import aliased


FichesProduits = aliased(Fiches)
FichesProjetMedias = aliased(Fiches)
FichesProjetTransmedias = aliased(Fiches)

NotesProduits = aliased(Notes)
NotesProjetMedias = aliased(Notes)
NotesProjetTransmedias = aliased(Notes)


Base = sqlalchemy.orm.declarative_base()
login_manager = LoginManager()
make_searchable(Base.metadata)  # this is needed for the search to work
app = Flask(__name__)
app.config.from_pyfile("config.py")
app.app_context().push()
squeeze = Squeeze(app)
cache.init_app(app)
engine = sa.create_engine(SQLALCHEMY_DATABASE_URI, pool_size=30, max_overflow=0)
sa.orm.configure_mappers()
ip_ban = IpBan(ban_count=30, ban_seconds=3600*24)
ip_ban.init_app(app)
ip_ban.ip_whitelist_add('127.0.0.1')
ip_ban.ip_whitelist_add('37.65.130.28')
session = orm.scoped_session(orm.sessionmaker(bind=engine))
csp = {
	'default-src': '\'self\'',
	'script-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'code.jquery.com',  'unpkg.com', '\'unsafe-inline\'', '\'unsafe-eval\''],
	'style-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'unpkg.com', '\'unsafe-inline\'', '\'unsafe-eval\'', 'fonts.googleapis.com'],
	'font-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'fonts.gstatic.com'],
	'img-src': ['\'self\'', 'picsum.photos', 'fastly.picsum.photos', 'data:'],
}
talisman = Talisman(app, strict_transport_security=True, force_https=True, content_security_policy=csp)
mail = Mail(app)
cors = CORS(app)
csrf = CSRFProtect(app)
login_manager.init_app(app)
assets = Environment(app)
auth_manager = AuthManager(app)
jwt = JWTManager(app)
Session(app)
dropzone = Dropzone(app)
css = Bundle("src/main.css", output="dist/main.css")
assets.register("css", css)
css.build()
app.secret_key = SECRET_KEY

def calculer_taux_completion_media(collection, pseudo):
	total_produits = session.query(Produits_Culturels). \
		join(Etre_Compose). \
		join(Projets_Medias). \
		filter_by(id_projets_medias=collection.id_projets_medias). \
		count()
	produits_possedes = session.query(Produits_Culturels). \
		join(Etre_Compose). \
		join(Projets_Medias). \
		filter_by(id_projets_medias=collection.id_projets_medias). \
		join(Posseder_C). \
		filter_by(pseudo=pseudo). \
		count()
	return (produits_possedes,total_produits) if total_produits else (0,0)

def calculer_taux_completion_transmedia(collection, pseudo):
	total_collection = session.query(Projets_Medias). \
		join(Contenir). \
		join(Projets_Transmedias). \
		filter_by(id_projets_transmedias=collection.id_projets_transmedias). \
		count()
	collections_possedes = session.query(Projets_Medias). \
		join(Contenir). \
		join(Projets_Transmedias). \
		filter_by(id_projets_transmedias=collection.id_projets_transmedias). \
		join(Posseder_M). \
		filter_by(pseudo=pseudo). \
		count()
	return (collections_possedes,total_collection) if total_collection else (0,0)


def web_or_app_auth(fn):
	@wraps(fn)
	def wrapper(*args, **kwargs):
		user = kwargs.get('user')
		if user is not None:
			@login_required
			@jwt_required(optional=True)
			def inner_wrapper(*args, **kwargs):
				if current_user.is_authenticated or get_jwt_identity():
					return fn(*args, **kwargs)
				return jsonify({"message": "Unauthorized access"}), 401

			return inner_wrapper(*args, **kwargs)
		else:
			return fn(*args, **kwargs)
	return wrapper

class GuestUser(AnonymousUserMixin):
	def __init__(self):
		self.pseudo = 'guest'
		self.adulte = False
		self.admin = False
		self.fondateur = False

@app.before_request
def load_user():
	if not hasattr(g, 'user'):
		g.user = GuestUser()
@app.errorhandler(413)
def too_large(e):
	return "Fichier trop volumineux", 413

@login_manager.user_loader
def load_user(pseudo):
	return session.execute(select(Utilisateurs).where(Utilisateurs.pseudo == pseudo)).scalar()

@app.route('/')
def index():
	nb_user = session.query(Utilisateurs).count()
	return render_template('public/index.html', nb_user=nb_user)
@app.route('/test')
def test():
	etre_associes = session.execute(select(Etre_Associe.nom_genres, Etre_Associe.nom_types_media).order_by(Etre_Associe.nom_genres)).all()
	typesmedia = session.execute(select(Types_Media.nom_types_media).order_by(Types_Media.nom_types_media)).all()
	max_files = config.DROPZONE_MAX_FILES
	max_file_size = config.DROPZONE_MAX_FILE_SIZE
	accepted_files = config.DROPZONE_ALLOWED_FILE_TYPE
	default_message = config.DROPZONE_DEFAULT_MESSAGE

	return render_template('public/test.html', etre_associes=etre_associes, typesmedia=typesmedia, max_files=max_files, max_file_size=max_file_size, accepted_files=accepted_files, default_message=default_message)
@app.route('/contribuer')
def contribuer():
	etre_associes = session.execute(select(Etre_Associe.nom_genres, Etre_Associe.nom_types_media).order_by(Etre_Associe.nom_genres)).all()
	typesmedia = session.execute(select(Types_Media.nom_types_media).order_by(Types_Media.nom_types_media)).all()
	max_files = config.DROPZONE_MAX_FILES
	max_file_size = config.DROPZONE_MAX_FILE_SIZE
	accepted_files = config.DROPZONE_ALLOWED_FILE_TYPE
	default_message = config.DROPZONE_DEFAULT_MESSAGE

	return render_template('public/ajout-fiche.html', etre_associes=etre_associes, typesmedia=typesmedia, max_files=max_files, max_file_size=max_file_size, accepted_files=accepted_files, default_message=default_message)

@app.route('/add-ean/by_fiche/', methods=['POST'])
@jwt_required(optional=False)
def add_ean_by_fiche():
	id_fiche = request.form.get('id_fiche')
	ean = request.form.get('ean')
	limite = request.form.get('limite')
	collector = request.form.get('collector')
	if id_fiche is None or ean is None or limite is None or collector is None:
		return jsonify({"message": "Paramètres manquants"}), 400
	#get the produit_culturel lnkked with this fiche and redirect
	produit_culturel = session.execute(select(Produits_Culturels).where(Produits_Culturels.id_fiches == id_fiche)).scalar()
	if produit_culturel is None or produit_culturel.id_produit_culturel is None:
		return jsonify({"message": "Fiche introuvable"}), 404
	else:
		#redirect the post data to the add_ean_by_produit route
		return redirect(url_for('add_ean_by_produit', id_produit=produit_culturel.id_produit_culturel, ean=ean, limite=limite, collector=collector))



@app.route('/add-ean/by_produit/', methods=['POST'])
@jwt_required(optional=False)
def add_ean_by_produit():
	#get the post data or get args if post data is empty
	id_produit = request.form.get('id_produit') if request.form.get('id_produit') is not None else request.args.get('id_produit')
	ean = request.form.get('ean') if request.form.get('ean') is not None else request.args.get('ean')
	limite = request.form.get('limite') if request.form.get('limite') is not None else request.args.get('limite')
	collector = request.form.get('collector') if request.form.get('collector') is not None else request.args.get('collector')
	if id_produit is None or ean is None or limite is None or collector is None:
		return jsonify({"message": "Paramètres manquants"}), 400
	#check if ean is valid
	if len(ean) == 10 and ean.isdigit():
		# conversion de l'ISBN-10 en ISBN-13
		ean = f'978{ean[:-1]}'
		#recalcul de la clé de contrôle
		ean += str((10 - (sum((3, 1)[i % 2] * int(c) for i, c in enumerate(ean))) % 10) % 10)
	if len(ean) != 13 or not ean.isdigit():
		return jsonify({"message": "EAN invalide"}), 400
	#recheck checksum
	if ean[:-1] != str((10 - (sum((3, 1)[i % 2] * int(c) for i, c in enumerate(ean))) % 10) % 10):
		return jsonify({"message": "EAN invalide"}), 400
	#check if the ean is already in the database
	ean_exists = session.execute(select(EAN13).where(EAN13.ean13 == ean)).scalar()
	if ean_exists is None:
		#if not, create it
		ean = EAN13(ean13=ean, limite=limite, collector=collector)
		session.add(ean)
		session.commit()
	etre_identifie_exists = session.execute(select(Etre_Identifie).where(and_(Etre_Identifie.id_produits_culturels == id_produit, Etre_Identifie.ean13 == ean))).scalar()
	if etre_identifie_exists is None:
		etre_identifie = Etre_Identifie(id_produits_culturels=id_produit, ean13=ean)
		session.add(etre_identifie)
		session.commit()
		return jsonify({"message": "EAN ajouté"}), 200
	else:
		return jsonify({"message": "EAN déjà ajouté pour ce produit"}), 400


@app.route('/get-by-ean/<ean>/', methods=['GET'])
def get_ean(ean):
	if len(ean) == 10 and ean.isdigit():
		# conversion de l'ISBN-10 en ISBN-13
		ean = f'978{ean[:-1]}'
		#recalcul de la clé de contrôle
		ean += str((10 - (sum((3, 1)[i % 2] * int(c) for i, c in enumerate(ean))) % 10) % 10)
	if len(ean) == 12 and ean.isdigit():
		#calcul de la clé de contrôle
		ean += str((10 - (sum((3, 1)[i % 2] * int(c) for i, c in enumerate(ean))) % 10) % 10)
	if len(ean) != 13 or not ean.isdigit():
		return jsonify({"message": "EAN invalide"}), 400
	ean_exists = session.execute(select(EAN13).where(EAN13.ean13 == ean)).scalar()
	if ean_exists is None:
		return jsonify({"message": "EAN introuvable"}), 404
	else:
		produit_culturel = session.execute(select(Produits_Culturels.id_produits_culturels, Produits_Culturels.date_sortie, Produits_Culturels.nom_types_media, Fiches.nom, Fiches.adulte,Fiches.concepteur, Fiches.url_image, EAN13.limite, EAN13.collector)
										   .select_from(EAN13) \
										   .join(Etre_Identifie, Etre_Identifie.ean13 == EAN13.ean13) \
										   .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Etre_Identifie.id_produits_culturels) \
										   .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches) \
										   .filter(EAN13.ean13 == ean) \
										   .group_by(Produits_Culturels.id_produits_culturels, Produits_Culturels.date_sortie, Produits_Culturels.nom_types_media, Fiches.nom, Fiches.adulte, Fiches.concepteur, Fiches.url_image, EAN13.limite, EAN13.collector) \
										   .order_by(desc(Produits_Culturels.id_produits_culturels)) \
										   .limit(5)).all()

		if produit_culturel is None:
			return jsonify({"message": "Fiche liée introuvable"}), 404

		else:
			#return all product info
			print(produit_culturel)
			return make_response(jsonify({'produits': [{ 'date_sortie': p.date_sortie, 'nom_types_media': p.nom_types_media, 'nom': p.nom, 'adulte': p.adulte, 'concepteur': p.concepteur, 'url_image': p.url_image, 'limite': p.limite, 'collector': p.collector} for p in produit_culturel]}), 200)




@app.route('/livesearch', methods=['GET','POST'])
def livesearch():
	title = request.args.get('q')
	isadulte = False
	verify_jwt_in_request(optional=True)
	if current_user.is_authenticated or get_jwt_identity() is not None:
		if current_user.is_authenticated:
			#check if user could access adult content
			isadulte = current_user.adulte
		elif get_jwt_identity() is not None:
			#check if user could access adult content
			isadulte = session.execute(select(Utilisateurs.adulte).where(Utilisateurs.pseudo == get_jwt_identity())).scalar()
	if title == '':
		return render_template('public/base.html')
	else:
		return function_search.search(title, isadulte, session)
@app.route('/recommandation/<int:id_fiche>/', methods=['GET'])
def recommandation(id_fiche):
	return recommandations.recommandations(id_fiche,5)
@app.route('/connexion', methods=['GET', 'POST'])
def login():
	client = request.args.get('client')
	method = request.method
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	if client == 'app' and method == 'POST':
		return function_login.login_app_post(session, auth_manager)
	elif client == 'app' and method == 'GET':
		return function_login.login_app_get()
	elif method == 'POST':
		return function_login.login_web_post(session)
	else:
		return function_login.login_web_get()
@app.route('/deconnexion')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

#ceci est simplement un exemple de route protégée par un token jwt
@app.route('/protected_route', methods=['GET', 'POST'])
@jwt_required(optional=False)
def protected_route():
	#return userid in json
	current_u = get_jwt_identity()
	return jsonify({'userid': current_u})

@app.route('/renew_jwt', methods=['GET'])
@jwt_required(refresh=True)
def renew_jwt():
	identity = get_jwt_identity()
	#if user is deleted or banned, return 403
	if session.execute(select(Utilisateurs.pseudo).where(and_(Utilisateurs.pseudo == identity, Utilisateurs.verifie is True, Utilisateurs.desactive is False))).scalar() is None:
		return jsonify({"message": "Le token d'identification ne peut pas être renouvelé pour cause de désactivation du compte."}), 403
	access_token = create_access_token(identity=identity)
	return jsonify(access_token=access_token)

@app.route('/test-totp', methods=['GET', 'POST'])
def test_totp():
	otp_secret = "ECTKRITZUCRCVGJTTAWAR2AE3MVNWJQR"
	totp = pyotp.TOTP(otp_secret)
	qr = pyqrcode.create(pyotp.totp.TOTP(otp_secret).provisioning_uri("matthieus701@gmail.com", issuer_name="Geek Compagnon"))
	qr_image = io.BytesIO()
	qr.png(qr_image, scale=5)
	qr_image.seek(0)
	#return file img
	return send_file(qr_image, mimetype='image/png')


@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
	if request.method == 'POST':
		return function_register.inscription_post(session)
	else:
		return function_register.inscription_get()

@app.route('/confirm_mail/<token>', methods=['GET'])
def confirm_mail(token):
	mail_checked = function_register.confirm_token(token)
	if mail_checked is False:
		flash("Le lien est invalide ou a expiré", "danger")
		return redirect(url_for('inscription'))
	else:
		hash_mail = bcrypt.hashpw(mail_checked.encode('utf-8'), BCRYPT_UNIQUE_SALT.encode('utf-8')).decode('utf-8')
		user = session.query(Utilisateurs).filter_by(hash_mail=hash_mail).first()
		user.verifie = True
		user.date_desactive = None
		session.commit()
		flash("Votre compte a bien été validé, vous pouvez à présent profiter du site!", "success")
		return redirect(url_for('login'))

@app.route('/ajouter-fiche', methods=['POST'])
def ajouter_fiche():
	radio_type = request.form.get('radio-type')
	if radio_type == "Culturel":
		return function_addfiche.ajouter_fiche_culturel(session)
	elif radio_type == "Média":
		return function_addfiche.ajouter_fiche_media(session)
	elif radio_type == "Transmédia":
		return function_addfiche.ajouter_fiche_transmedia(session)
	else:
		return make_response(jsonify({'message': 'Type de fiche inconnu ou non saisi'}), 400)

@app.route('/ajouter-lien', methods=['GET', 'POST'])
def ajouter_lien():
	if request.method == 'POST':
		radio_type = request.args.get('radio-type')
		id_culturel = request.args.get('id_culturel') if request.args.get('id_culturel') is not None else ""
		id_media = request.args.get('id_media') if request.args.get('id_media') is not None else ""
		id_transmedia = request.args.get('id_transmedia') if request.args.get('id_transmedia') is not None else ""
		ordre = request.args.get('ordre') if request.args.get('ordre') is not None else ""
		if radio_type == "Culturel-Média":
			if id_culturel == "" or id_media == "":
				return make_response(jsonify({'message': 'Paramètres manquants'}), 400)
			if ordre == "":
				ordre = 1000 #arbitrary value, for placing not orderable at the end of the list
			if not ordre.isdigit() or not id_culturel.isdigit() or not id_media.isdigit():
				return make_response(jsonify({'message': 'Paramètres incorrects'}), 400)

			# check if product and media exist
			if session.execute(select(Produits_Culturels.id_produits_culturels).where(Produits_Culturels.id_produits_culturels == id_culturel)).scalar() is None:
				return make_response(jsonify({'message': 'Le produit culturel n\'existe pas'}), 400)
			if session.execute(select(Projets_Medias.id_projets_medias).where(Projets_Medias.id_projets_medias == id_media)).scalar() is None:
				return make_response(jsonify({'message': 'Le projet média n\'existe pas'}), 400)
			#check if link already exists
			if session.execute(select(Etre_Compose.id_produits_culturels).where(and_(Etre_Compose.id_produits_culturels == id_culturel, Etre_Compose.id_projets_medias == id_media))).scalar() is not None:
				return make_response(jsonify({'message': 'Le lien entre ces deux éléments existe déjà'}), 400)
			etre_compose = Etre_Compose(id_produits_culturels=id_culturel, id_projets_medias=id_media, ordre=ordre, verifie=False)
			session.add(etre_compose)
			session.commit()
			return make_response(jsonify({'message': 'Lien ajouté entre le produit et le média, il va être verifie par l\'équipe de modération'}), 200)

		if radio_type == "Média-Transmédia":
			if id_media == "" or id_transmedia == "":
				return make_response(jsonify({'message': 'Paramètres manquants'}), 400)
			if not id_media.isdigit() or not id_transmedia.isdigit():
				return make_response(jsonify({'message': 'Paramètres incorrects'}), 400)
			#check if media and transmedia exist
			if session.execute(select(Projets_Medias.id_projets_medias).where(Projets_Medias.id_projets_medias == id_media)).scalar() is None:
				return make_response(jsonify({'message': 'Le projet média n\'existe pas'}), 400)
			if session.execute(select(Projets_Transmedias.id_projets_transmedias).where(Projets_Transmedias.id_projets_transmedias == id_transmedia)).scalar() is None:
				return make_response(jsonify({'message': 'Le projet transmédia n\'existe pas'}), 400)
			#check if link already exists
			if session.execute(select(Contenir.id_projets_medias).where(and_(Contenir.id_projets_medias == id_media, Contenir.id_projets_transmedias == id_transmedia))).scalar() is not None:
				return make_response(jsonify({'message': 'Le lien entre ces deux éléments existe déjà'}), 400)
			contenir = Contenir(id_projets_medias=id_media, id_projets_transmedias=id_transmedia, verifie=False)
			session.add(contenir)
			session.commit()
			return make_response(jsonify({'message': 'Lien ajouté entre le projet média et le projet transmedia, il va être verifie par l\'équipe de modération'}), 200)
	if request.method == 'GET':
		return render_template('public/ajouter-lien.html')


@app.route('/fiche/<int:id_fiche>', methods=['GET'])
def fiche(id_fiche):
	client = request.args.get('client') if request.args.get('client') is not None else ""
	#redirect to produit culturel, projet media or projet transmedia linked withe the id_fiche
	if session.execute(select(Produits_Culturels.id_fiches).where(Produits_Culturels.id_fiches == id_fiche)).scalar() is not None:
		id_produit_culturel = session.execute(select(Produits_Culturels.id_produits_culturels).where(Produits_Culturels.id_fiches == id_fiche)).scalar()
		return redirect(f"{url_for('produit_culturel', id_produit_culturel=int(id_produit_culturel), client=client)}")
	elif session.execute(select(Projets_Medias.id_fiches).where(Projets_Medias.id_fiches == id_fiche)).scalar() is not None:
		id_projet_media = session.execute(select(Projets_Medias.id_projets_medias).where(Projets_Medias.id_fiches == id_fiche)).scalar()
		return redirect(f"{url_for(f'projet_media', id_projet_media=int(id_projet_media), client=client)}")
	elif session.execute(select(Projets_Transmedias.id_fiches).where(Projets_Transmedias.id_fiches == id_fiche)).scalar() is not None:
		id_projet_transmedia = session.execute(select(Projets_Transmedias.id_projets_transmedias).where(Projets_Transmedias.id_fiches == id_fiche)).scalar()
		return redirect(f"{url_for(f'projet_transmedia', id_projet_transmedia=int(id_projet_transmedia), client=client)}")
	else:
		if client == "":
			return render_template('public/404.html')
		else:
			return jsonify({'message': 'La fiche n\'existe pas'}), 400

@app.route('/produit_culturel/<int:id_produit_culturel>', methods=['GET'])
@app.route('/produit_culturel/')
def produit_culturel(id_produit_culturel):
	client = request.args.get('client') if request.args.get('client') is not None else ""
	user_agent = request.headers.get('User-Agent')
	id_produit_culturel = request.args.get('id_produit_culturel') if request.args.get('id_produit_culturel') is not None else id_produit_culturel
	return function_produit_culturel.produit_culturel_app(session, id_produit_culturel, client, user_agent)

@app.route('/projet_media/<int:id_projet_media>', methods=['GET'])
@app.route('/projet_media/')
def projet_media(id_projet_media):
	client = request.args.get('client') if request.args.get('client') is not None else ""
	user_agent = request.headers.get('User-Agent')
	id_projet_media = request.args.get('id_projet_media') if request.args.get('id_projet_media') is not None else id_projet_media
	return function_projet_media.projet_media_app(session, id_projet_media, client, user_agent)

@app.route('/projet_transmedia/<int:id_projet_transmedia>', methods=['GET'])
@app.route('/projet_transmedia/')
def projet_transmedia(id_projet_transmedia):
	client = request.args.get('client') if request.args.get('client') is not None else ""
	user_agent = request.headers.get('User-Agent')
	id_projet_transmedia = request.args.get('id_projet_transmedia') if request.args.get('id_projet_transmedia') is not None else id_projet_transmedia
	return function_projet_transmedia.projet_transmedia_app(session, id_projet_transmedia, client, user_agent)



@app.route('/bibliotheque/<idtype>/<idfiltre>/<int:numstart>', methods=['GET'])
@app.route('/bibliotheque/<idtype>/<idfiltre>', methods=['GET'])
@app.route('/bibliotheque/<idtype>/<int:numstart>', methods=['GET'])
@app.route('/bibliotheque/<int:numstart>', methods=['GET'])
@app.route('/bibliotheque/<idfiltre>', methods=['GET'])
@app.route('/bibliotheque/', methods=['GET'])
@app.route('/bibliotheque', methods=['GET'])
def bibliotheque(idtype="all", numstart=0, idfiltre=""):
	client = request.args.get('client')
	return function_bibliotheque.bibliotheque_app(session, idtype, idfiltre, numstart, client)

@app.route('/collection/<idtype>/<idfiltre>/<int:numstart>', methods=['GET'])
@app.route('/collection/<idtype>/<idfiltre>', methods=['GET'])
@app.route('/collection/<idtype>/<int:numstart>', methods=['GET'])
@app.route('/collection/<int:numstart>', methods=['GET'])
@app.route('/collection/<idfiltre>', methods=['GET'])
@app.route('/collection/', methods=['GET'])
@app.route('/collection', methods=['GET'])
def collection(idtype="all", numstart=0, idfiltre=""):
	client = request.args.get('client')
	return function_collection.collection_app(session, idtype, idfiltre, numstart, client)

@app.route('/ma-bibliotheque/<idtype>/<idfiltre>/<int:numstart>', methods=['GET'])
@app.route('/ma-bibliotheque/<idtype>/<int:numstart>', methods=['GET'])
@app.route('/ma-bibliotheque/<user>/<idtype>/<idfiltre>/<int:numstart>', methods=['GET'])
@app.route('/ma-bibliotheque/<user>/<idtype>/<int:numstart>', methods=['GET'])
@app.route('/ma-bibliotheque/<user>/<idtype>/<idfiltre>', methods=['GET'])
@app.route('/ma-bibliotheque/<user>/<idtype>', methods=['GET'])
@app.route('/ma-bibliotheque/<user>/<idfiltre>', methods=['GET'])
@app.route('/ma-bibliotheque/', methods=['GET'])
@app.route('/ma-bibliotheque', methods=['GET'])
def my_bibliotheque(idtype="all", numstart=0, idfiltre="", user=""):
	client = request.args.get('client')
	return function_mybibliotheque.mybibliotheque_app(session, idtype, idfiltre, numstart, client, requested_user=user)

@app.route('/ma-collection/<idtype>/<idfiltre>/<int:numstart>', methods=['GET'])
@app.route('/ma-collection/<idtype>/<int:numstart>', methods=['GET'])
@app.route('/ma-collection/<user>/<idtype>/<idfiltre>/<int:numstart>', methods=['GET'])
@app.route('/ma-collection/<user>/<idtype>/<int:numstart>', methods=['GET'])
@app.route('/ma-collection/<user>/<idtype>/<idfiltre>', methods=['GET'])
@app.route('/ma-collection/<user>/<idtype>', methods=['GET'])
@app.route('/ma-collection/<user>/<idfiltre>', methods=['GET'])
@app.route('/ma-collection/', methods=['GET'])
@app.route('/ma-collection', methods=['GET'])
def my_collection(idtype="all", numstart=0, idfiltre="", user=""):
	client = request.args.get('client')
	return function_mycollection.mycollection_app(session, idtype, idfiltre, numstart, client, user)

@app.route('/utilisateur/<user>/stats/<idtype>/', methods=['GET'])
@app.route('/utilisateur/<user>/stats/<idtype>', methods=['GET'])
def stats(user, idtype):
	if user not in session.query(Utilisateurs.pseudo).filter(Utilisateurs.verifie == True, Utilisateurs.desactive == False, Utilisateurs.pseudo == user).first():
		return make_response(jsonify({'error': 'Utilisateur inconnu'}), 404)
	client = request.args.get('client')
	return function_user_stats.stats(session, user, client, idtype)

@app.route('/utilisateur/<user>/settings/', methods=['GET'])
@app.route('/utilisateur/<user>/settings', methods=['GET'])
@web_or_app_auth
def settings(user):
	client = request.args.get('client')
	return function_user_settings.settings(session, user, client)

@app.route('/activate_totp', methods=['POST'])
@web_or_app_auth
def activate_totp():
	otp_code = request.form.get('code')
	token = request.form.get('token')
	secret = request.form.get('secret')
	temp_secret = session.query(Temp_Secrets).get(token)
	if not temp_secret:
		return make_response(jsonify({'error': 'Invalid token'}), 400)
	secret = temp_secret.secret
	if pyotp.TOTP(secret).verify(otp_code):
		# The OTP code is correct
		current_user.otp_secret = secret
		session.delete(temp_secret)  # Remove the secret from the table
		session.commit()
		# Update the user in the database and return success
		user_to_update = session.query(Utilisateurs).filter(Utilisateurs.pseudo == current_user.pseudo).first()
		user_to_update.otp_secret = secret
		session.commit()
		return make_response(jsonify({'status': 'ok'}), 200)
	else:
		# The OTP code is incorrect
		return make_response(jsonify({'error': 'Invalid OTP code'}), 400)
@app.route('/generate_otp', methods=['GET'])
@web_or_app_auth
def generate_otp():
	secret = pyotp.random_base32()
	token = uuid4()  # Function to generate a random token
	temp_secret = Temp_Secrets(token, secret)
	session.add(temp_secret)
	session.commit()
	return jsonify({'secret': secret, 'token': token})

@app.route('/delete_user_data', methods=['GET'])
@web_or_app_auth
def delete_user_data():
	client = request.args.get('client')
	verify_jwt_in_request()
	if client == "app":
		user = get_jwt_identity()
		user = session.query(Utilisateurs).filter(Utilisateurs.pseudo == user).first()
	else:
		user = session.query(Utilisateurs).filter(Utilisateurs.pseudo == current_user.pseudo).first()
	try:

		# Supprimez toutes les lignes liées à l'utilisateur dans chaque table
		session.query(Posseder_T).filter_by(pseudo=user.pseudo).delete()
		session.query(Posseder_M).filter_by(pseudo=user.pseudo).delete()
		session.query(Posseder_C).filter_by(pseudo=user.pseudo).delete()
		session.query(Threads).filter_by(pseudo=user.pseudo).delete()
		session.query(Commentaires).filter_by(pseudo=user.pseudo).delete()
		session.query(Notes).filter_by(pseudo=user.pseudo).delete()
		session.query(Avis).filter_by(pseudo=user.pseudo).delete()

		# Soumettez la transaction
		session.commit()
	except:
		# Si une erreur se produit, faites un rollback
		session.rollback()
		raise

	flash('Données utilisateur supprimées avec succès', 'success')

	if client == "app":
		return jsonify({'message': 'Données utilisateur supprimées avec succès'})

	return redirect("/utilisateur/"+ current_user.pseudo +"/settings/")

@app.route('/deactivate_account', methods=['GET'])
@web_or_app_auth
def deactivate_account():
	try:
		# set the desactive attribute to True
		current_user.desactive = True
		current_user.verifie = False

		# update the date_desactive attribute
		current_user.date_desactive = datetime.datetime.utcnow()

		# anonymize the pseudo, hash_mail and hash_mdp fields
		anon_id = str(uuid.uuid4())  # generate a unique id for anonymization
		anon_pseudo = f"anon_{anon_id}"
		current_user.pseudo = anon_pseudo
		current_user.hash_mail = generate_password_hash(f"anon_{anon_id}@geek-compagnon.io")
		current_user.hash_mdp = generate_password_hash(f"anon_{anon_id}")

		if current_user.biographie:
			current_user.biographie = "Utilisateur désactivé"

		if current_user.otp_secret:
			current_user.otp_secret = None

		# replace user image by default image
		current_user.url_image = '/static/images/default-profile.png'

		# anonymize related data in Posseder_T table
		for posseder_t in current_user.posseder_t:
			posseder_t.pseudo = anon_pseudo

		# anonymize related data in Posseder_M table
		for posseder_m in current_user.posseder_m:
			posseder_m.pseudo = anon_pseudo

		# anonymize related data in Posseder_C table
		for posseder_c in current_user.posseder_c:
			posseder_c.pseudo = anon_pseudo

		# anonymize related data in Threads table
		for thread in current_user.threads:
			thread.pseudo = anon_pseudo

		# anonymize related data in Commentaires table
		for commentaire in current_user.commentaires:
			commentaire.pseudo = anon_pseudo

		# anonymize related data in Notes table
		for note in current_user.notes:
			note.pseudo = anon_pseudo

		# anonymize related data in Avis table
		for avis in current_user.avis:
			avis.pseudo = anon_pseudo

		# commit changes to the database
		session.commit()

		flash('Your account has been deactivated. All your personal data has been anonymized.', 'success')

	except session as e:  # Utiliser SQLAlchemyError
		session.rollback()
		flash('An error occurred while deactivating your account.', 'error')
		print(e)

	logout_user()
	resp = make_response(redirect(url_for('index')))
	resp.set_cookie('remember_token', '', expires=0)

	# redirect the user to the home page
	return redirect(url_for('index'))
@app.route('/update_user', methods=['POST'])
@web_or_app_auth
def update_user():
	user = session.query(Utilisateurs).filter(Utilisateurs.pseudo == current_user.pseudo).first()

	# update regular form fields
	user.notification = request.form.get('notification') == 'on'
	user.profil_public = request.form.get('profil_public') == 'on'
	user.adulte = request.form.get('adulte') == 'on'

	session.commit()  # commit the changes

	# process image
	if 'dropz' in request.files:
		url_image = request.files['dropz']
		file_signature = url_image.read(8)

		if not file_signature.startswith(Image_Signature.JPEG) and not file_signature.startswith(Image_Signature.PNG):
			return make_response(jsonify({'message': "Le fichier n'est pas une image dans un format accepté"}), 400)

		if file_signature.startswith(Image_Signature.PNG):
			url_image = Image.open(url_image)
			url_image = url_image.convert('RGB')
		elif file_signature.startswith(Image_Signature.JPEG):
			url_image = Image.open(url_image)

		if url_image.height < 300 or url_image.width < 300:
			return make_response(
				jsonify({'message': "L'image est trop petite, elle doit faire au minimum 300x300 pixels"}), 400)

		# ensure user image folder exists
		image_folder = f'static/images/utilisateurs/{user.pseudo}'
		if not os.path.exists(image_folder):
			os.makedirs(image_folder)

		url_image.seek(0)
		url_image.save(f'{image_folder}/profile.jpg')

		saved_image = Image.open(f'{image_folder}/profile.jpg')
		wpercent = (460 / float(saved_image.size[0]))
		hsize = int((float(saved_image.size[1]) * float(wpercent)))
		saved_image.thumbnail((460, hsize), Image.LANCZOS)
		saved_image.save(f'{image_folder}/profile.jpg', optimize=True, quality=95, progressive=True)

		# update user image url
		user.url_image = os.path.join('static', 'images', 'utilisateurs', user.pseudo, "profile.jpg").replace("\\", "/")

		#add first slash if missing
		if not user.url_image.startswith("/"):
			user.url_image = "/" + user.url_image

		session.commit()  # commit the changes again

	return jsonify({'message': 'Profil mis à jour avec succès'}), 200

@app.route('/delete_user_notes', methods=['GET'])
@web_or_app_auth
def delete_user_notes():
	client = request.args.get('client')
	try:
		if client == 'app':
			user = get_jwt_identity()
			user_notes = session.query(Notes).filter(Notes.pseudo == user).all()
		else:
			user_notes = session.query(Notes).filter(Notes.pseudo == current_user.pseudo).all()

		if len(user_notes) > 0:
			for note in user_notes:
				session.delete(note)

			session.commit()
			flash('Vos notes ont été supprimées avec succès.', 'success')
		else:
			flash('Vous n\'avez aucune note à supprimer.', 'info')

	except Exception as e:
		flash('Une erreur est survenue lors de la suppression de vos notes. Veuillez réessayer plus tard.', 'error')
		print(e)
	if client == 'app':
		return jsonify({'message': 'Vos notes ont été supprimées avec succès.'}), 200

	return redirect("/utilisateur/" + current_user.pseudo + "/settings/")

@app.route('/delete_user_avis', methods=['GET'])
@web_or_app_auth
def delete_user_avis():
	client = request.args.get('client')
	try:
		if client == 'app':
			user = get_jwt_identity()
			user_reviews = session.query(Avis).filter(Avis.pseudo == user).all()
		else:
			user_reviews = session.query(Avis).filter(Avis.pseudo == current_user.pseudo).all()

		if len(user_reviews) > 0:
			for review in user_reviews:
				session.delete(review)

			session.commit()
			flash('Vos avis ont été supprimés avec succès.', 'success')
		else:
			flash('Vous n\'avez aucun avis à supprimer.', 'info')

	except Exception as e:
		flash('Une erreur est survenue lors de la suppression de vos avis. Veuillez réessayer plus tard.', 'error')
		print(e)

	if client == 'app':
		return jsonify({'message': 'Vos avis ont été supprimés avec succès.'}), 200

	return redirect("/utilisateur/" + current_user.pseudo + "/settings/")
@app.route('/utilisateur/<user>/<int:numstart>', methods=['GET'])
@app.route('/utilisateur/<user>/<int:numstart>/', methods=['GET'])
@app.route('/utilisateur/<user>/', methods=['GET'])
@app.route('/utilisateur/<user>', methods=['GET'])
@cache.cached(timeout=50)
def user(user, numstart=0):
	client = request.args.get('client')
	# Récupérez tous les projets transmedia pour l'utilisateur avec leurs collections associées
	produits_culturels = (
		session.query(Posseder_C)
		.join(Produits_Culturels, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels)
		.join(FichesProduits, Produits_Culturels.id_fiches == FichesProduits.id_fiches)
		.outerjoin(NotesProduits, FichesProduits.id_fiches == NotesProduits.id_fiches)
		.join(Etre_Compose, Produits_Culturels.id_produits_culturels == Etre_Compose.id_produits_culturels)
		.join(Projets_Medias, Etre_Compose.id_projets_medias == Projets_Medias.id_projets_medias)
		.join(FichesProjetMedias, Projets_Medias.id_fiches == FichesProjetMedias.id_fiches)
		.outerjoin(NotesProjetMedias, FichesProjetMedias.id_fiches == NotesProjetMedias.id_fiches)
		.join(Contenir, Projets_Medias.id_projets_medias == Contenir.id_projets_medias)
		.join(Projets_Transmedias, Contenir.id_projets_transmedias == Projets_Transmedias.id_projets_transmedias)
		.join(FichesProjetTransmedias, Projets_Transmedias.id_fiches == FichesProjetTransmedias.id_fiches)
		.outerjoin(NotesProjetTransmedias, FichesProjetTransmedias.id_fiches == NotesProjetTransmedias.id_fiches)
		.filter(Posseder_C.pseudo == user)
		.options(joinedload(Posseder_C.produits_culturels, innerjoin=True)
				 .subqueryload(Produits_Culturels.etre_compose)
				 .joinedload(Etre_Compose.projets_medias)
				 .subqueryload(Projets_Medias.contenir)
				 .joinedload(Contenir.projets_transmedias))
		.order_by(Posseder_C.date_ajout.desc())
		.limit(10).offset(numstart)
		.all()
	)

	nombre_projets_transmedia = session.query(Contenir).filter(Contenir.id_projets_medias == Etre_Compose.id_projets_medias).count() #for keep cache, request is splited

	# Récupérez les favoris de l'utilisateur

	favoris_produits = (
		session.query(Produits_Culturels)
		.join(Fiches, Produits_Culturels.id_fiches == Fiches.id_fiches)
		.join(Avis, Fiches.id_fiches == Avis.id_fiches)
		.filter(Avis.pseudo == user, Avis.favori == True)
		.all()
	)

	favoris_projets_medias = (
		session.query(Projets_Medias)
		.join(Fiches, Projets_Medias.id_fiches == Fiches.id_fiches)
		.join(Avis, Fiches.id_fiches == Avis.id_fiches)
		.filter(Avis.pseudo == user, Avis.favori == True)
		.all()
	)

	favoris_projets_transmedias = (
		session.query(Projets_Transmedias)
		.join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)
		.join(Avis, Fiches.id_fiches == Avis.id_fiches)
		.filter(Avis.pseudo == user, Avis.favori == True)
		.all()
	)

	favoris_produits_data = [
		{
			'nom_produit': produit.fiche.nom,
			'url_image': produit.fiche.url_image,
			'favori': next((avis.favori for avis in produit.fiche.avis if avis.pseudo == user), False),
		} for produit in favoris_produits
	]

	favoris_projets_medias_data = [
		{
			'nom_projet_media': projet_media.fiche.nom,
			'url_image': projet_media.fiche.url_image,
			'favori': next((avis.favori for avis in projet_media.fiche.avis if avis.pseudo == user), False),
		} for projet_media in favoris_projets_medias
	]

	favoris_projets_transmedias_data = [
		{
			'nom_projet_transmedia': projet_transmedia.fiche.nom,
			'url_image': projet_transmedia.fiche.url_image,
			'favori': next((avis.favori for avis in projet_transmedia.fiche.avis if avis.pseudo == user), False),
		} for projet_transmedia in favoris_projets_transmedias
	]

	data = []
	for row in produits_culturels:
		product_data = {
			'nom_produit': row.produits_culturels.fiche.nom,
			'url_image': row.produits_culturels.fiche.url_image,
			'note': next((note.note for note in row.produits_culturels.fiche.notes if note.pseudo == user), ''),
			'favori': next((avis.favori for avis in row.produits_culturels.fiche.avis if avis.pseudo == user), False),
			'projet_media': []
		}

		for etre_compose in row.produits_culturels.etre_compose[:10]:
			produits_possedes, total_produits = calculer_taux_completion_media(etre_compose.projets_medias, user)
			collection_data = {
				'nom_projet_media': etre_compose.projets_medias.fiche.nom,
				'url_image': etre_compose.projets_medias.fiche.url_image,
				'note': next((note.note for note in etre_compose.projets_medias.fiche.notes if note.pseudo == user), ''),
				'favori': next((avis.favori for avis in etre_compose.projets_medias.fiche.avis if avis.pseudo == user), False),
				'taux_completion': str(produits_possedes) + "/" + str(total_produits),
				'truncated': len(etre_compose.projets_medias.contenir) > 10,
				'projet_transmedia': []
			}

			for contenir in etre_compose.projets_medias.contenir[:10]:
				collections_possedes, total_collection = calculer_taux_completion_transmedia(contenir.projets_transmedias, user)
				collection_imbriquee_data = {
					'nom_projet_transmedia': contenir.projets_transmedias.fiche.nom,
					'url_image': contenir.projets_transmedias.fiche.url_image,
					'note': next((note.note for note in contenir.projets_transmedias.fiche.notes if note.pseudo == user), ''),
					'favori': next((avis.favori for avis in contenir.projets_transmedias.fiche.avis if avis.pseudo == user), False),
					'taux_completion': str(collections_possedes) + "/" + str(total_collection),
					'truncated': nombre_projets_transmedia > 10
				}
				collection_data['projet_transmedia'].append(collection_imbriquee_data)

			product_data['projet_media'].append(collection_data)

		data.append(product_data)

	if client == "app":
		# Ajouter les favoris à votre structure de données existante
		data = {
			'produits_culturels': data,  # Vos données existantes
			'favoris_produits': favoris_produits_data,
			'favoris_projets_medias': favoris_projets_medias_data,
			'favoris_projets_transmedias': favoris_projets_transmedias_data,
		}
		return make_response(jsonify(data), 200)
	else:
		if numstart == 0:
			return render_template('public/user.html', data=data, user=user, numstart=numstart, favoris_produits=favoris_produits, favoris_projets_medias=favoris_projets_medias, favoris_projets_transmedias=favoris_projets_transmedias)
		else:
			return render_template('public/infine-scroll-user.html', data=data, numstart=numstart)






if __name__ == "__main__":
	app.run(port=7777, ssl_context=(os.path.dirname(os.path.abspath(__file__)) + "/SSLcertificate.crt", os.path.dirname(os.path.abspath(__file__)) + "/SSLprivatekey.key"), host="0.0.0.0", debug=True)

