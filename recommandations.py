from flask import jsonify

from config import Config
from  dataclass import *
import sqlalchemy as sa
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
engine = sa.create_engine(Config.SQLALCHEMY_DATABASE_URI  , pool_size=30, max_overflow=0)
session = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine))
from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop

def recommandations(id_produit: int, nb_recommandations: int):
    #create a content based recommandation algorithm
    #get produit culturel, fiche, noms alternatif, genres, type media from id_produits_culturels in database
    #if the id_produits_culturels is not in the database, return an error

    if not session.query(Produits_Culturels).filter_by(id_produits_culturels=id_produit).first():
        return jsonify({"error": "La fiche produit exigée n'est pas présente dans nos données"}), 404

    if nb_recommandations > 10:
        return jsonify({"error": "le nombre de recommandations est superieur à 10"}), 400

    base = (
        session.query(
            Produits_Culturels.id_produits_culturels,
            Produits_Culturels.date_sortie,
            Fiches.nom,
            Fiches.synopsis,
            Fiches.adulte,
            Fiches.concepteur,
            sa.func.string_agg(sa.func.distinct(Noms_Alternatifs.nom_alternatif), " "),
            Types_Media.nom_types_media,
            sa.func.string_agg(sa.func.distinct(Genres.nom_genres), " "),
        )
        .select_from(Produits_Culturels)
        .join(Fiches)
        .join(Etre_Defini)
        .join(Types_Media)
        .join(Genres)
        .outerjoin(Nommer_C)
        .outerjoin(Noms_Alternatifs)
        .group_by(
            Produits_Culturels.id_produits_culturels,
            Fiches.id_fiches,
            Types_Media.nom_types_media,
        )
        .all()
    )
    #create a dataframe with pandas
    df = pd.DataFrame(base, columns=["id","date_sortie", "nom", "synopsis", "adulte", "concepteur", "noms_alternatifs", "nom_types_media", "genres"])
    # Sélectionner les colonnes qui contiennent les features à utiliser pour la recommandation
    features = ['nom', 'concepteur', 'synopsis', 'nom_types_media', 'genres', 'noms_alternatifs', 'adulte', 'date_sortie']
    data = df[features]

    # Remplacer les valeurs null par une chaîne vide
    data = data.fillna('')

    # Formater les données pour qu'elles soient utilisables par l'algorithme des k plus proches voisins
    data['genres'] = data['genres'].apply(lambda x: x.split())
    data['noms_alternatifs'] = data['noms_alternatifs'].apply(lambda x: x.split())
    data['synopsis'] = data['synopsis'].apply(lambda x: x.split())
    data['nom_types_media'] = data['nom_types_media'].apply(lambda x: x.split())
    data['nom'] = data['nom'].apply(lambda x: x.split())
    data['concepteur'] = data['concepteur'].apply(lambda x: x.split())
    data['adulte'] = data['adulte'].astype(str).apply(lambda x: x.split())
    data['date_sortie'] = data['date_sortie'].astype(str).apply(lambda x: x.split())

    new_df = data['concepteur'] + data['synopsis'] + data['nom_types_media'] + data['genres'] + data['noms_alternatifs'] + data['adulte'] + data['date_sortie']
    new_df = new_df.apply(lambda x: ' '.join(x))

    #create a new dataframe with pandas with 3 columns
    df2 = pd.DataFrame(columns=['id', 'nom', 'features'])
    df2['id'] = df['id'].astype(str)
    df2['nom'] = df['nom']
    df2['features'] = new_df

    df2['features'] = df2['features'].apply(lambda x: x.lower())

    cv = CountVectorizer(max_features=5000, stop_words=list(fr_stop))
    X = cv.fit_transform(df2['features']).toarray()

    # Calculer la distance entre les produits culturels
    cosine_sim = cosine_similarity(X)

    # Récupérer l'index du produit culturel
    index = df2[df2['id'] == str(id_produit)].index[0]

    # Récupérer les distances entre le produit culturel et les autres produits culturels
    distances = list(enumerate(cosine_sim[index]))

    # Trier les distances par ordre décroissant
    distances = sorted(distances, key=lambda x: x[1], reverse=True)

    # Récupérer les indices des k plus proches voisins
    indices = [i[0] for i in distances[1:nb_recommandations+1]]

    # Récupérer les k plus proches voisins
    recommandations = df2.iloc[indices]

    return jsonify({'recommandations': recommandations['id'].tolist()})
