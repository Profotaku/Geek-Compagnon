from flask import jsonify

from config import *
from  dataclass import *
import sqlalchemy as sa
import pandas as pd
from sqlalchemy import orm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
engine = sa.create_engine(SQLALCHEMY_DATABASE_URI  , pool_size=30, max_overflow=0)
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
            sa.func.avg(Notes.note).label('moyenne_notes'),
            sa.func.count(Avis.id_avis).filter(Avis.favori == True).label('nombre_favori'),
            sa.func.count(Avis.id_avis).filter(Avis.avis_popularite == 1).label('nombre_sur_mediatise'),
            sa.func.count(Avis.id_avis).filter(Avis.avis_popularite == -1).label('nombre_sous_mediatise'),
            sa.func.count(Avis.id_avis).filter(Avis.avis_popularite == 0).label('nombre_neutre_mediatise'),
            sa.func.count(Avis.id_avis).filter(Avis.avis_cote == 1).label('nombre_sur_note'),
            sa.func.count(Avis.id_avis).filter(Avis.avis_cote == -1).label('nombre_sous_note'),
            sa.func.count(Avis.id_avis).filter(Avis.avis_cote == 0).label('nombre_neutre_note'),
        )
        .select_from(Produits_Culturels)
        .join(Fiches)
        .join(Etre_Defini)
        .join(Types_Media)
        .join(Genres)
        .outerjoin(Nommer_C)
        .outerjoin(Noms_Alternatifs)
        .outerjoin(Notes)
        .outerjoin(Avis)
        .group_by(
            Produits_Culturels.id_produits_culturels,
            Fiches.id_fiches,
            Types_Media.nom_types_media,
        )
        .all()
    )
    #create a dataframe with pandas
    df = pd.DataFrame(base, columns=["id","date_sortie", "nom", "synopsis", "adulte", "concepteur", "noms_alternatifs", "nom_types_media", "genres", "moyenne_notes", "nombre_favori", "ratio_sur_mediatise", "ratio_sous_mediatise", "ratio_neutre_mediatise", "ratio_sur_note", "ratio_sous_note", "ratio_neutre_note"])
    # Sélectionner les colonnes qui contiennent les features à utiliser pour la recommandation
    features = ['nom', 'concepteur', 'synopsis', 'nom_types_media', 'genres', 'noms_alternatifs', 'adulte', 'date_sortie', 'moyenne_notes', 'nombre_favori', 'ratio_sur_mediatise', 'ratio_sous_mediatise', 'ratio_neutre_mediatise', 'ratio_sur_note', 'ratio_sous_note', 'ratio_neutre_note']
    data = df[features]

    # Prétraiter les données ratio

    data.loc[:, 'ratio_sur_mediatise'] = data['ratio_sur_mediatise'] / (data['ratio_sur_mediatise'] + data['ratio_sous_mediatise'] + data['ratio_neutre_mediatise'])
    data.loc[:, 'ratio_sous_mediatise'] = data['ratio_sous_mediatise'] / (data['ratio_sur_mediatise'] + data['ratio_sous_mediatise'] + data['ratio_neutre_mediatise'])
    data.loc[:, 'ratio_neutre_mediatise'] = data['ratio_neutre_mediatise'] / (data['ratio_sur_mediatise'] + data['ratio_sous_mediatise'] + data['ratio_neutre_mediatise'])
    data.loc[:, 'ratio_sur_note'] = data['ratio_sur_note'] / (data['ratio_sur_note'] + data['ratio_sous_note'] + data['ratio_neutre_note'])
    data.loc[:, 'ratio_sous_note'] = data['ratio_sous_note'] / (data['ratio_sur_note'] + data['ratio_sous_note'] + data['ratio_neutre_note'])
    data.loc[:, 'ratio_neutre_note'] = data['ratio_neutre_note'] / (data['ratio_sur_note'] + data['ratio_sous_note'] + data['ratio_neutre_note'])

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
    data['moyenne_notes'] = data['moyenne_notes'].astype(str).apply(lambda x: x.split())
    data['nombre_favori'] = data['nombre_favori'].astype(str).apply(lambda x: x.split())
    data['ratio_sur_mediatise'] = data['ratio_sur_mediatise'].astype(str).apply(lambda x: x.split())
    data['ratio_sous_mediatise'] = data['ratio_sous_mediatise'].astype(str).apply(lambda x: x.split())
    data['ratio_neutre_mediatise'] = data['ratio_neutre_mediatise'].astype(str).apply(lambda x: x.split())
    data['ratio_sur_note'] = data['ratio_sur_note'].astype(str).apply(lambda x: x.split())
    data['ratio_sous_note'] = data['ratio_sous_note'].astype(str).apply(lambda x: x.split())
    data['ratio_neutre_note'] = data['ratio_neutre_note'].astype(str).apply(lambda x: x.split())

    new_df = data['concepteur'] + data['synopsis'] + data['nom_types_media'] + data['genres'] + data['noms_alternatifs'] + data['adulte'] + data['date_sortie'] + data['moyenne_notes'] + data['nombre_favori'] + data['ratio_sur_mediatise'] + data['ratio_sous_mediatise'] + data['ratio_neutre_mediatise'] + data['ratio_sur_note'] + data['ratio_sous_note'] + data['ratio_neutre_note']
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
    index_cult = df2[df2['id'] == str(id_produit)].index[0]

    # Récupérer les distances entre le produit culturel et les autres produits culturels
    distances = list(enumerate(cosine_sim[index_cult]))

    # Trier les distances par ordre décroissant
    distances = sorted(distances, key=lambda x: x[1], reverse=True)

    # Récupérer les indices et les scores des k plus proches voisins
    nearest_neighbors = distances[1:nb_recommandations + 1]

    # Récupérer les k plus proches voisins et leurs scores
    recommandations = [{'id': df2.iloc[i[0]]['id'], 'score': i[1]} for i in nearest_neighbors]

    return jsonify({'recommandations': recommandations})

