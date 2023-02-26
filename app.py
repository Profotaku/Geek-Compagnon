# -*- coding: utf-8 -*-
import flask
import sqlalchemy_searchable
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_file
from flask_caching import Cache
import sqlalchemy as sa  # ORM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm, or_, and_, select, join, outerjoin
from sqlalchemy_searchable import make_searchable, search
from flask_wtf.csrf import CSRFProtect # CSRF protection
from flask_mailman import Mail  # API for sending emails
from flask_cors import CORS  # prevent CORS attacks
from flask_bcrypt import Bcrypt  # hash passwords
from flask_login import LoginManager  # user session management
from huey import RedisHuey, crontab  # task queue
from flask_ipban import IpBan  # IP ban
from sqlalchemy import literal_column
from sqlalchemy.sql.operators import op
import os
import sqlalchemy.sql.functions
from sqlalchemy_utils.types.pg_composite import psycopg2
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.neighbors import NearestNeighbors, KNeighborsClassifier
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import sklearn
from sklearn.preprocessing import MultiLabelBinarizer
from flask_assets import Bundle, Environment
from sklearn.pipeline import Pipeline
from flask_login import login_user, logout_user, current_user, login_required
from flask_pyjwt import AuthManager, require_token, current_token
from flask_talisman import Talisman # security headers
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_session import Session
import io


from config import Config
from dataclass import *
import recommandations
import function_login
import pyotp
import pyqrcode

Base = sqlalchemy.orm.declarative_base()
login_manager = LoginManager()
make_searchable(Base.metadata)  # this is needed for the search to work
app = Flask(__name__)
app.config.from_object(Config)
cache = Cache(app)
engine = sa.create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_size=30, max_overflow=0)
sa.orm.configure_mappers()
ip_ban = IpBan(ban_count=30, ban_seconds=3600*24)
ip_ban.init_app(app)
ip_ban.ip_whitelist_add('127.0.0.1')
session = orm.scoped_session(orm.sessionmaker(bind=engine))
csp = {
    'default-src': '\'self\'',
    'img-src': [ '\'self\'', 'picsum.photos', 'fastly.picsum.photos',  'anilist.co'],
    'script-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net'],
    'style-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net'],
    'font-src': ['\'self\'', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net'],

}
talisman = Talisman(app, strict_transport_security=True, force_https=True, content_security_policy=csp)
mail = Mail(app)
cors = CORS(app)
csrf = CSRFProtect(app)
bcrypt = Bcrypt(app)
login_manager.init_app(app)
assets = Environment(app)
auth_manager = AuthManager(app)
jwt = JWTManager(app)
Session(app)
css = Bundle("src/main.css", output="dist/main.css")
assets.register("css", css)
css.build()
app.secret_key = Config.SECRET_KEY

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
    genres = session.execute(select(Genres.nom_genres).order_by(Genres.nom_genres)).all()
    return render_template('public/test.html', genres=genres)
@app.route('/livesearch', methods=['GET','POST'])
def livesearch():
    title = "Haruhi"
    #escape the user input to prevent sql injection
    #search = request.form.get('search')

    if title == '':
        return render_template('public/base.html')
    else:
        print(title)
        result = session.execute(select((Produits_Culturels.id_produits_culturels, Fiches.nom, Fiches.synopsis, Produits_Culturels.date_sortie, Fiches.url_image, Noms_Alternatifs.nom_alternatif, Types_Media.nom_types_media, Etre_Compose.ordre, Projets_Medias.id_projets_medias, Projets_Medias.nom_types_media)\
            .select_from(Produits_Culturels)\
            .join(Types_Media)\
            .outerjoin(Nommer_C, Noms_Alternatifs, Etre_Compose, Projets_Medias)\
            .filter(or_(Fiches.nom.match(title), Noms_Alternatifs.nom_alternatif.match(title)))\
            .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
            .distinct(Produits_Culturels.id_produits_culturels).all()))
        for r in result:
            print(r)
        return "ok"
@app.route('/recommandation/<int:id_fiche>/', methods=['GET'])
def recommandation(id_fiche):
    return recommandations.recommandations(id_fiche,5)
@app.route('/connexion' , methods=['GET', 'POST'])
def login():
    client = request.args.get('client')
    method = request.method
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if client == 'app' and method == 'POST':
        return function_login.login_app_post(bcrypt, session, auth_manager)
    elif client == 'app' and method == 'GET':
        return function_login.login_app_get()
    elif method == 'POST':
        return function_login.login_web_post(bcrypt, session)
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
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)
@app.route('/navbar', methods=['GET'])
def navbar():
    return render_template('public/navbar.html', connected=current_user.is_authenticated)

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


