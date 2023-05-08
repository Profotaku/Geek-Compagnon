# -*- coding: utf-8 -*-
import flask
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_file, make_response
from flask_caching import Cache
import sqlalchemy as sa  # ORM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm, or_, and_, select, join, outerjoin, text, func, desc
from sqlalchemy_searchable import make_searchable, search
from flask_wtf.csrf import CSRFProtect # CSRF protection
from flask_mailman import Mail  # API for sending emails
from flask_cors import CORS  # prevent CORS attacks
import bcrypt
from flask_login import LoginManager  # user session management
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
import pyotp
import pyqrcode

Base = sqlalchemy.orm.declarative_base()
login_manager = LoginManager()
make_searchable(Base.metadata)  # this is needed for the search to work
app = Flask(__name__)
app.config.from_pyfile("config.py")
app.app_context().push()
squeeze = Squeeze(app)
cache = Cache(app)
engine = sa.create_engine(SQLALCHEMY_DATABASE_URI, pool_size=30, max_overflow=0)
sa.orm.configure_mappers()
ip_ban = IpBan(ban_count=30, ban_seconds=3600*24)
ip_ban.init_app(app)
ip_ban.ip_whitelist_add('127.0.0.1')
session = orm.scoped_session(orm.sessionmaker(bind=engine))
csp = {
    'default-src': '\'self\'',
    'script-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'code.jquery.com',  'unpkg.com', '\'unsafe-inline\'', '\'unsafe-eval\''],
    'style-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'unpkg.com', '\'unsafe-inline\'', '\'unsafe-eval\'', 'fonts.googleapis.com'],
    'font-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'fonts.gstatic.com'],
    'img-src': ['\'self\'', 'picsum.photos', 'fastly.picsum.photos', 'anilist.co', 'data:'],
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

#session.execute(text("""CREATE EXTENSION IF NOT EXISTS pg_trgm;"""))

def web_or_app_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = kwargs.get('user')
        if user is None:
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
@app.errorhandler(413)
def too_large(e):
    return "Fichier trop volumineux", 413

@login_manager.user_loader
def load_user(pseudo):
    return session.execute(select(Utilisateurs).where(Utilisateurs.pseudo == pseudo)).scalar()

@app.route('/')
def index():
    nb_user = session.query(Utilisateurs).count()
    return render_template('public/index.html', nb_user=nb_user, connected=current_user.is_authenticated)
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
@jwt_required()
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
        return redirect(f"{url_for(f'produit_culturel/{str(id_produit_culturel)}')}?client={client}")
    elif session.execute(select(Projets_Medias.id_fiches).where(Projets_Medias.id_fiches == id_fiche)).scalar() is not None:
        id_projet_media = session.execute(select(Projets_Medias.id_projets_medias).where(Projets_Medias.id_fiches == id_fiche)).scalar()
        return redirect(f"{url_for(f'projet_media/{str(id_projet_media)}')}?client={client}")
    elif session.execute(select(Projets_Transmedias.id_fiches).where(Projets_Transmedias.id_fiches == id_fiche)).scalar() is not None:
        id_projet_transmedia = session.execute(select(Projets_Transmedias.id_projets_transmedias).where(Projets_Transmedias.id_fiches == id_fiche)).scalar()
        return redirect(f"{url_for(f'projet_transmedia/{str(id_projet_transmedia)}')}?client={client}")
    else:
        if client == "":
            return render_template('public/404.html')
        else:
            return jsonify({'message': 'La fiche n\'existe pas'}), 400


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
    return function_mybibliotheque.mybibliotheque_app(session, idtype, idfiltre, numstart, client, user)

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





if __name__ == "__main__":
    app.run(port=7777, ssl_context=(os.path.dirname(os.path.abspath(__file__)) + "/SSLcertificate.crt", os.path.dirname(os.path.abspath(__file__)) + "/SSLprivatekey.key"), host="0.0.0.0", debug=True)

