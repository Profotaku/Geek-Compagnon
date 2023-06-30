from flask import jsonify

from config import *
from dataclass import *
import sqlalchemy as sa
import pandas as pd
from sqlalchemy import orm
engine = sa.create_engine(SQLALCHEMY_DATABASE_URI, pool_size=30, max_overflow=0)
session = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine))
import spacy
nlp = spacy.load('fr_core_news_sm')
import torch
import numpy as np
from annoy import AnnoyIndex

# Chargez le tokenizer et le modèle BERT
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('huawei-noah/TinyBERT_General_4L_312D')
model = AutoModel.from_pretrained('huawei-noah/TinyBERT_General_4L_312D')

# Specify the dimensionality of your vectors. For TinyBERT, it's 312.
f = 312
t = AnnoyIndex(f, 'angular')

# Function to preprocess text
def preprocess(text):
    # Créer un document spaCy
    doc = nlp(text)

    # Générer la liste des lemmes pour chaque mot du document
    lemmas = [token.lemma_ for token in doc]

    # Retourner les lemmes sous forme de chaîne de caractères
    return ' '.join(lemmas)


def bert_encode(text):
    # Encode le texte avec le tokenizer BERT
    encoded_input = tokenizer(text, padding=True, truncation=True, max_length=512, return_tensors='pt')

    # Passez l'entrée encodée à travers le modèle BERT pour obtenir les vecteurs de caractéristiques
    with torch.no_grad():
        features = model(**encoded_input)

    # Prenez la moyenne des embeddings pour obtenir une seule représentation vectorielle pour chaque texte
    features = features[0].mean(dim=1)

    # Squeeze pour supprimer les dimensions de taille 1
    features = features.squeeze()

    return features.numpy()


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
        .outerjoin(Etre_Defini)
        .join(Types_Media)
        .outerjoin(Genres)
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

    #Créer un nouveau dataframe avec les colonnes id, nom, synopsis et features, les 3 premières étant à renvoyer à l'utilisateur et la dernière étant utilisée pour la recommandation
    df2 = pd.DataFrame(columns=['id', 'nom', 'synopsis', 'features'])
    df2['id'] = df['id'].astype(str)
    df2['nom'] = df['nom']
    df2['synopsis'] = df['synopsis']
    df2['features'] = new_df

    # After creating the new_df and df2
    df2['features'] = df2['features'].apply(lambda x: x.lower())
    df2['features'] = df2['features'].apply(preprocess)
    df2['features'] = df2['features'].apply(bert_encode)

    # Prepare Annoy index
    f = len(df2['features'][0])  # Length of item vector that will be indexed
    t = AnnoyIndex(f, 'angular')  # Length of item vector that will be indexed and metric

    for i, vector in enumerate(df2['features']):
        t.add_item(i, vector)

    t.build(10)  # 10 trees

    # Get the index of the product
    index_cult = df2[df2['id'] == str(id_produit)].index[0]

    # Use Annoy to get nearest neighbors
    nearest_neighbors = t.get_nns_by_item(index_cult, nb_recommandations)


    # Construct recommendations
    recommandations = [
        {'id': df2.iloc[i]['id'], 'nom': df2.iloc[i]['nom'], 'score': 1 - float(t.get_distance(index_cult, i))} for i in
        nearest_neighbors[1:]]

    return jsonify({'recommandations': recommandations})

