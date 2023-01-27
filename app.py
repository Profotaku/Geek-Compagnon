# -*- coding: utf-8 -*-
import sqlalchemy_searchable
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_caching import Cache
import sqlalchemy as sa  # ORM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm, or_, and_, select, join, outerjoin
from sqlalchemy_searchable import make_searchable, search
from flask_wtf import FlaskForm  # CSRF protection
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

from config import Config
from dataclass import *
import recommandations

Base = sqlalchemy.orm.declarative_base()
login_manager = LoginManager()
make_searchable(Base.metadata)  # this is needed for the search to work
app = Flask(__name__)
app.config.from_object(Config)
cache = Cache(app)
engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'], pool_size=30, max_overflow=0)
sa.orm.configure_mappers()
ip_ban = IpBan(ban_count=30, ban_seconds=3600*24)
ip_ban.init_app(app)
ip_ban.ip_whitelist_add('127.0.0.1')
session = orm.scoped_session(orm.sessionmaker(bind=engine))
mail = Mail(app)
cors = CORS(app)
bcrypt = Bcrypt(app)
login_manager.init_app(app)
assets = Environment(app)
css = Bundle("src/main.css", output="dist/main.css")
assets.register("css", css)
css.build()


@app.errorhandler(413)
def too_large(e):
    return "Fichier trop volumineux", 413

@login_manager.user_loader
def load_user(pseudo):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return Utilisateurs.query.get(str(pseudo))

@app.route('/')
@cache.cached(timeout=24*60*60)
def index():
    nb_user = session.query(Utilisateurs).count()
    return render_template('public/index.html', nb_user=nb_user)
@app.route('/test')
def test():
    return render_template('public/test.html')
@app.route('/livesearch', methods=['GET','POST'])
def livesearch():
    title = "Haruhi"
    #escape the user input to prevent sql injection
    #search = request.form.get('search')

    if title == '':
        return render_template('public/base.html')
    else:
        print(title)
        result = session.query(Produits_Culturels.id_produits_culturels, Fiches.nom, Fiches.synopsis, Produits_Culturels.date_sortie, Fiches.url_image, Noms_Alternatifs.nom_alternatif, Types_Media.nom_types_media, Etre_Compose.ordre, Projets_Medias.id_projets_medias, Projets_Medias.nom_types_media)\
            .select_from(Produits_Culturels)\
            .join(Types_Media)\
            .outerjoin(Nommer_C, Noms_Alternatifs, Etre_Compose, Projets_Medias)\
            .filter(or_(Fiches.nom.match(title), Noms_Alternatifs.nom_alternatif.match(title)))\
            .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
            .distinct(Produits_Culturels.id_produits_culturels).all()
        for r in result:
            print(r)
        return "ok"
@app.route('/recommandation', methods=['GET','POST'])
def recommandation():
    return recommandations.recommandations(2,1)