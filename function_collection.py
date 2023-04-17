from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal
from config import *
def collection_app(session, idtype, idfiltre, numstart, client):
    if type(numstart) == int:
        if session.query(Types_Media).filter_by(nom_types_media=idtype).first() is not None or idtype == "all":
            if idtype == "all":
                idtype = session.execute(select(Types_Media.nom_types_media).select_from(Types_Media).distinct(Types_Media.nom_types_media)).all()
                idtype = [row[0] for row in idtype]
            if idfiltre in ["", "date-ajout", "top-consultation", "top-note", "top-favoris", "sur-mediatise", "sous-mediatise", "sur-note", "sous-note"]:
                if type(idtype) != list:
                    idtype = [idtype]
                if idfiltre == "" or idfiltre == "date-ajout":
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .join(Types_Media)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Types_Media.nom_types_media.in_(idtype))\
                        .distinct(Projets_Medias.id_projets_medias)\
                        .order_by(Projets_Medias.id_projets_medias.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.verifie == True)\
                        .distinct(Projets_Transmedias.id_projets_transmedias)\
                        .order_by(Projets_Transmedias.id_projets_transmedias.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.fiches_id_fiches.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "top-consultation":
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Fiches.consultation,  Types_Media.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .join(Types_Media)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Types_Media.nom_types_media.in_(idtype))\
                        .order_by(Fiches.consultation.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Fiches.consultation)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.verifie == True)\
                        .order_by(Fiches.consultation.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.fiches_consultation.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "top-note":
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, Notes.note_0,  Notes.note_1, Notes.note_2, Notes.note_3, Notes.note_4, Notes.note_5, Notes.note_6, Notes.note_7, Notes.note_8, Notes.note_9, Notes.note_10, func.avg((Notes.note_0 + Notes.note_1 + Notes.note_2 + Notes.note_3 + Notes.note_4 + Notes.note_5 + Notes.note_6 + Notes.note_7 + Notes.note_8 + Notes.note_9 + Notes.note_10)/11).label('moyenne_notes'), Types_Media.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .join(Types_Media)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .filter(Projets_Medias.id_notes == Notes.id_notes)\
                        .group_by(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, Notes.note_0, Notes.note_1, Notes.note_2, Notes.note_3, Notes.note_4, Notes.note_5, Notes.note_6, Notes.note_7, Notes.note_8, Notes.note_9, Notes.note_10, Types_Media.nom_types_media) \
                        .order_by(desc('moyenne_notes'))
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, Notes.note_0,  Notes.note_1, Notes.note_2, Notes.note_3, Notes.note_4, Notes.note_5, Notes.note_6, Notes.note_7, Notes.note_8, Notes.note_9, Notes.note_10, func.avg((Notes.note_0 + Notes.note_1 + Notes.note_2 + Notes.note_3 + Notes.note_4 + Notes.note_5 + Notes.note_6 + Notes.note_7 + Notes.note_8 + Notes.note_9 + Notes.note_10)/11).label('moyenne_notes'))\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.verifie == True) \
                        .filter(Projets_Transmedias.id_notes == Notes.id_notes)\
                        .group_by(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, Notes.note_0, Notes.note_1, Notes.note_2, Notes.note_3, Notes.note_4, Notes.note_5, Notes.note_6, Notes.note_7, Notes.note_8, Notes.note_9, Notes.note_10)\
                        .order_by(desc('moyenne_notes'))
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.moyenne_notes.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "top-favoris":
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Fiches.cmpt_favori, Types_Media.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .join(Types_Media)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Fiches.cmpt_favori.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Fiches.cmpt_favori)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.verifie == True) \
                        .order_by(Fiches.cmpt_favori.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.fiches_cmpt_favori.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "sur-mediatise":
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.trop_popularite, Types_Media.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .join(Types_Media)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Medias.id_avis == Avis.id_avis) \
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Avis.trop_popularite.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.trop_popularite)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Transmedias.id_avis == Avis.id_avis) \
                        .filter(Projets_Transmedias.verifie == True) \
                        .order_by(Avis.trop_popularite.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.avis_trop_popularite.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "sous-mediatise":
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.manque_popularite, Types_Media.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .join(Types_Media)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Medias.id_avis == Avis.id_avis) \
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Avis.manque_popularite.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.manque_popularite)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Transmedias.id_avis == Avis.id_avis) \
                        .filter(Projets_Transmedias.verifie == True) \
                        .order_by(Avis.manque_popularite.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.avis_manque_popularite.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "sur-note":
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.trop_cote,  Types_Media.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .join(Types_Media)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Medias.id_avis == Avis.id_avis) \
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Avis.trop_cote.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.trop_cote)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Transmedias.id_avis == Avis.id_avis) \
                        .filter(Projets_Transmedias.verifie == True) \
                        .order_by(Avis.trop_cote.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.avis_trop_cote.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "sous-note":
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.manque_cote,  Types_Media.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .join(Types_Media)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Medias.id_avis == Avis.id_avis) \
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Avis.manque_cote.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.manque_cote)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Transmedias.id_avis == Avis.id_avis) \
                        .filter(Projets_Transmedias.verifie == True) \
                        .order_by(Avis.manque_cote.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.avis_manque_cote.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                else:
                    return make_response(jsonify({'message': 'filtre inconnu'}), 400)
                collection_reponse = []
                if client == "app":
                    collection_reponse.append({'collection': [{'id': c[0], 'nom': c[1], 'url_image': c[2], 'adulte': c[4]} for c in collection]})
                    #add fields "consultation" in 'collection' if idfiltre == "top-consultation"
                    for i in range(len(collection_reponse[0]['collection'])):
                        collection_reponse[0]['collection'][i]['consultation'] = collection[i][len(collection[i])-2] if idfiltre == "top-consultation" else None
                        collection_reponse[0]['collection'][i]['note'] = round(float(collection[i][len(collection[i])-2]),2) if idfiltre == "top-note" else None
                        collection_reponse[0]['collection'][i]['favori'] = collection[i][len(collection[i])-2] if idfiltre == "top-favoris" else None
                        collection_reponse[0]['collection'][i]['sur-mediatise'] = collection[i][len(collection[i])-2] if idfiltre == "sur-mediatise" else None
                        collection_reponse[0]['collection'][i]['sous-mediatise'] = collection[i][len(collection[i])-2] if idfiltre == "sous-mediatise" else None
                        collection_reponse[0]['collection'][i]['sur-note'] = collection[i][len(collection[i])-2] if idfiltre == "sur-note" else None
                        collection_reponse[0]['collection'][i]['sous-note'] = collection[i][len(collection[i])-2] if idfiltre == "sous-note" else None
                    return make_response(jsonify(collection_reponse), 200)
                else:
                    return collection
            else:
                return make_response(jsonify({'message': 'filtre inconnu'}), 400)
        else:
            return make_response(jsonify({'message': 'type inconnu'}), 400)
    else:
        return make_response(jsonify({'message': 'cette valeur doit être un nombre entier'}), 400)