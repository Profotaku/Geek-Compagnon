from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal
from config import *
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    verify_jwt_in_request
def collection_app(session, idtype, idfiltre, numstart, client):
    if type(numstart) == int:
        isadulte = False
        verify_jwt_in_request(optional=True)
        if current_user.is_authenticated:
            isadulte = current_user.adulte
        if get_jwt_identity() is not None:
            isadulte = session.execute(select(Utilisateurs.adulte).where(Utilisateurs.pseudo == get_jwt_identity())).scalar()
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
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Projets_Medias.nom_types_media.in_(idtype))\
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
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Projets_Medias.nom_types_media.in_(idtype))\
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
                    moyenne_notes = func.avg(Notes.note).label('moyenne_notes')
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, moyenne_notes, Projets_Medias.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Projets_Medias.nom_types_media.in_(idtype)) \
                        .filter(Projets_Medias.id_fiches == Notes.id_fiches)\
                        .group_by(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, Projets_Medias.nom_types_media) \
                        .order_by(moyenne_notes.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, moyenne_notes)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.verifie == True) \
                        .filter(Projets_Transmedias.id_fiches == Notes.id_fiches)\
                        .group_by(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes)\
                        .order_by(moyenne_notes.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.moyenne_notes.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "top-favoris":
                    nombre_favori = func.count(Avis.id_avis).filter(Avis.favori == True).label('nombre_favori')
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_favori, Projets_Medias.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Medias.id_fiches == Avis.id_fiches)\
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Projets_Medias.nom_types_media.in_(idtype)) \
                        .group_by(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, Projets_Medias.nom_types_media) \
                        .order_by(nombre_favori.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_favori)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Avis.id_fiches)\
                        .filter(Projets_Transmedias.verifie == True) \
                        .group_by(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis)\
                        .order_by(nombre_favori.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.nombre_favori.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "sur-mediatise":
                    nombre_sur_mediatise = func.count(Avis.id_avis).filter(Avis.avis_popularite == 1).label('nombre_sur_mediatise')
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_sur_mediatise, Projets_Medias.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches) \
                        .filter(Fiches.id_fiches == Avis.id_fiches) \
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Projets_Medias.nom_types_media.in_(idtype)) \
                        .group_by(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, Projets_Medias.nom_types_media) \
                        .order_by(nombre_sur_mediatise.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_sur_mediatise)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Fiches.id_fiches == Avis.id_fiches) \
                        .filter(Projets_Transmedias.verifie == True) \
                        .group_by(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis)\
                        .order_by(nombre_sur_mediatise.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.nombre_sur_mediatise.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "sous-mediatise":
                    nombre_sous_mediatise = func.count(Avis.id_avis).filter(Avis.avis_popularite == -1).label('nombre_sous_mediatise')
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_sous_mediatise, Projets_Medias.nom_types_media) \
                        .select_from(Projets_Medias) \
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches) \
                        .filter(Fiches.id_fiches == Avis.id_fiches) \
                        .filter(Projets_Medias.verifie == True) \
                        .filter(Projets_Medias.nom_types_media.in_(idtype)) \
                        .group_by(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, Projets_Medias.nom_types_media) \
                        .order_by(nombre_sous_mediatise.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_sous_mediatise) \
                        .select_from(Projets_Transmedias) \
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Fiches.id_fiches == Avis.id_fiches) \
                        .filter(Projets_Transmedias.verifie == True) \
                        .group_by(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis) \
                        .order_by(nombre_sous_mediatise.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.nombre_sous_mediatise.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "sur-note":
                    nombre_sur_note = func.count(Avis.id_avis).filter(Avis.avis_cote == 1).label('nombre_sur_note')
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_sur_note, Projets_Medias.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Medias.id_fiches == Avis.id_fiches) \
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Projets_Medias.nom_types_media.in_(idtype)) \
                        .group_by(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, Projets_Medias.nom_types_media)\
                        .order_by(nombre_sur_note.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_sur_note)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Transmedias.id_fiches == Avis.id_fiches) \
                        .filter(Projets_Transmedias.verifie == True) \
                        .group_by(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis)\
                        .order_by(nombre_sur_note.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.nombre_sur_note.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                elif idfiltre == "sous-note":
                    nombre_sous_note = func.count(Avis.id_avis).filter(Avis.avis_cote == -1).label('nombre_sous_note')
                    media_query = session.query(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_sous_note, Projets_Medias.nom_types_media)\
                        .select_from(Projets_Medias)\
                        .filter(Projets_Medias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Medias.id_fiches == Avis.id_fiches) \
                        .filter(Projets_Medias.verifie == True)\
                        .filter(Projets_Medias.nom_types_media.in_(idtype)) \
                        .group_by(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, Projets_Medias.nom_types_media)\
                        .order_by(nombre_sous_note.desc())
                    transmedia_query = session.query(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis, nombre_sous_note)\
                        .select_from(Projets_Transmedias)\
                        .join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)\
                        .filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
                        .filter(Projets_Transmedias.id_fiches == Avis.id_fiches) \
                        .filter(Projets_Transmedias.verifie == True) \
                        .group_by(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.id_avis)\
                        .order_by(nombre_sous_note.desc())
                    #add column "type" to the query
                    transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                    collection_query = union_all(media_query, transmedia_query)
                    collection_query = collection_query.order_by(collection_query.c.nombre_sous_note.desc()).limit(10).offset(numstart)
                    collection = session.execute(collection_query).all()
                else:
                    return make_response(jsonify({'message': 'filtre inconnu'}), 400)
                collection_reponse = []
                if not isadulte:
                    collection = [c for c in collection if c[4] == False]
                if client == "app":
                    collection_reponse.append({'collection': [{'id': c[0], 'nom': c[1], 'url_image': c[2], 'adulte': c[4]} for c in collection]})
                    for i in range(len(collection_reponse[0]['collection'])):
                        collection_reponse[0]['collection'][i]['consultation'] = collection[i][len(collection[i])-2] if idfiltre == "top-consultation" else None
                        collection_reponse[0]['collection'][i]['note'] = round(float(collection[i][len(collection[i])-2]),2) if idfiltre == "top-note" else None
                        collection_reponse[0]['collection'][i]['favori'] = collection[i][len(collection[i])-2] if idfiltre == "top-favoris" else None
                        collection_reponse[0]['collection'][i]['sur-mediatise'] = collection[i][len(collection[i])-2] if idfiltre == "sur-mediatise" else None
                        collection_reponse[0]['collection'][i]['sous-mediatise'] = collection[i][len(collection[i])-2] if idfiltre == "sous-mediatise" else None
                        collection_reponse[0]['collection'][i]['sur-note'] = collection[i][len(collection[i])-2] if idfiltre == "sur-note" else None
                        collection_reponse[0]['collection'][i]['sous-note'] = collection[i][len(collection[i])-2] if idfiltre == "sous-note" else None
                    return make_response(jsonify(collection_reponse), 200)
                if len(idtype) > 1:
                    idtype = "all"
                else:
                    idtype = idtype[0]
                if numstart == 0:
                    return render_template('public/collection.html', collection=collection, idtype=idtype, idfiltre=idfiltre, numstart=numstart)
                else:
                    return render_template('public/infine-scroll-collection.html', collection=collection, idtype=idtype, idfiltre=idfiltre, numstart=numstart)
            else:
                return make_response(jsonify({'message': 'filtre inconnu'}), 400)
        else:
            return make_response(jsonify({'message': 'type inconnu'}), 400)
    else:
        return make_response(jsonify({'message': 'cette valeur doit être un nombre entier'}), 400)