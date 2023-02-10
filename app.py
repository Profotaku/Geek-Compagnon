# -*- coding: utf-8 -*-
import sqlalchemy_searchable
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
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
from flask_pyjwt import AuthManager, require_token

from config import Config
from dataclass import *
import recommandations
import function_login

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
mail = Mail(app)
cors = CORS(app)
csrf = CSRFProtect(app)
bcrypt = Bcrypt(app)
login_manager.init_app(app)
assets = Environment(app)
auth_manager = AuthManager(app)
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
@app.route('/recommandation', methods=['GET','POST'])
def recommandation():
    return recommandations.recommandations(2,1)
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
@require_token()
def protected_route():
    return jsonify({'message': 'This is only available for people with valid tokens.'})


