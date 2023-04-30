from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal
from config import *
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    verify_jwt_in_request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

def mycollection_app(session, idtype, idfiltre, numstart, client, user):
    isadulte = False
    verify_jwt_in_request(optional=True)
    if user == "" and current_user.is_authenticated or get_jwt_identity() is not None:
        if current_user.is_authenticated:
            user = current_user.pseudo
            isadulte = current_user.adulte
        else:
            user = get_jwt_identity()
            isadulte = session.execute(select(Utilisateurs.adulte).where(Utilisateurs.pseudo == get_jwt_identity())).scalar()
    if session.query(Utilisateurs).filter_by(pseudo=user).first() is not None or user is None:
        if session.query(Utilisateurs.profil_public).filter_by(pseudo=user).first()[0] or (user == current_user.pseudo if current_user.is_authenticated else False) or user == get_jwt_identity():
            if type(numstart) == int:
                if session.query(Types_Media).filter_by(nom_types_media=idtype).first() is not None or idtype == "all":
                    if idtype == "all":
                        idtype = session.execute(select(Types_Media.nom_types_media).select_from(Types_Media).distinct(Types_Media.nom_types_media)).all()
                        idtype = [row[0] for row in idtype]
                    if idfiltre in ["", "date-ajout", "top-note", "favori", "sur-mediatise", "sous-mediatise", "sur-note", "sous-note", "physiquement", "virtuellement", "souhaite", "limite", "collector"]:
                        if type(idtype) != list:
                            idtype = [idtype]
                        if idfiltre == "" or idfiltre == "date-ajout":
                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo,Posseder_M.note,Posseder_M.favori, Posseder_M.date_ajout, Types_Media.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .join(Types_Media, Types_Media.nom_types_media == Projets_Medias.nom_types_media)\
                            .filter(Types_Media.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .distinct(Posseder_M.date_ajout, Posseder_M.id_projets_medias)\
                            .order_by(Posseder_M.date_ajout.desc())\
                            .order_by(Posseder_M.id_projets_medias.desc())
                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo,Posseder_T.note,Posseder_T.favori, Posseder_T.date_ajout)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .distinct(Posseder_T.date_ajout, Posseder_T.id_projets_transmedias)\
                            .order_by(Posseder_T.date_ajout.desc())\
                            .order_by(Posseder_T.id_projets_transmedias.desc())
                            # add column "type" to the query
                            transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                            collection_query = union_all(media_query, transmedia_query)
                            collection_query = collection_query.order_by(collection_query.c.posseder_m_date_ajout.desc()).limit(10).offset(numstart)
                            my_collection = session.execute(collection_query).all()
                        elif idfiltre == "top-note":
                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo,Posseder_M.note,Posseder_M.favori, Posseder_M.date_ajout, Types_Media.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .join(Types_Media, Types_Media.nom_types_media == Projets_Medias.nom_types_media)\
                            .filter(Types_Media.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .distinct(Posseder_M.note, Posseder_M.id_projets_medias)\
                            .order_by(Posseder_M.note.desc())\
                            .order_by(Posseder_M.id_projets_medias.desc())
                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo,Posseder_T.note,Posseder_T.favori, Posseder_T.date_ajout)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .distinct(Posseder_T.note, Posseder_T.id_projets_transmedias)\
                            .order_by(Posseder_T.note.desc())\
                            .order_by(Posseder_T.id_projets_transmedias.desc())
                            # add column "type" to the query
                            transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                            collection_query = union_all(media_query, transmedia_query)
                            collection_query = collection_query.order_by(collection_query.c.posseder_m_note.desc()).limit(10).offset(numstart)
                            my_collection = session.execute(collection_query).all()
                        elif idfiltre == "favori":
                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo,Posseder_M.note,Posseder_M.favori, Posseder_M.date_ajout, Types_Media.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .join(Types_Media, Types_Media.nom_types_media == Projets_Medias.nom_types_media)\
                            .filter(Types_Media.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Posseder_M.favori == True)\
                            .distinct(Posseder_M.favori, Posseder_M.id_projets_medias) \
                            .order_by(Posseder_M.id_projets_medias.desc())
                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo,Posseder_T.note,Posseder_T.favori, Posseder_T.date_ajout)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Posseder_T.favori == True)\
                            .distinct(Posseder_T.favori, Posseder_T.id_projets_transmedias)\
                            .order_by(Posseder_T.id_projets_transmedias.desc())
                            # add column "type" to the query
                            transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                            collection_query = union_all(media_query, transmedia_query)
                            collection_query = collection_query.order_by(collection_query.c.posseder_m_date_ajout.desc()).limit(10).offset(numstart)
                            my_collection = session.execute(collection_query).all()
                        elif idfiltre == "sur-mediatise":
                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo,Posseder_M.note,Posseder_M.favori, Posseder_M.date_ajout, Types_Media.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .join(Types_Media, Types_Media.nom_types_media == Projets_Medias.nom_types_media)\
                            .filter(Types_Media.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Posseder_M.avis_popularite == True)\
                            .distinct(Posseder_M.avis_popularite, Posseder_M.id_projets_medias) \
                            .order_by(Posseder_M.id_projets_medias.desc())
                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo,Posseder_T.note,Posseder_T.favori, Posseder_T.date_ajout)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Posseder_T.avis_popularite == True)\
                            .distinct(Posseder_T.avis_popularite, Posseder_T.id_projets_transmedias)\
                            .order_by(Posseder_T.id_projets_transmedias.desc())
                            # add column "type" to the query
                            transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                            collection_query = union_all(media_query, transmedia_query)
                            collection_query = collection_query.order_by(collection_query.c.posseder_m_date_ajout.desc()).limit(10).offset(numstart)
                            my_collection = session.execute(collection_query).all()
                        elif idfiltre == "sous-mediatise":
                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo,Posseder_M.note,Posseder_M.favori, Posseder_M.date_ajout, Types_Media.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .join(Types_Media, Types_Media.nom_types_media == Projets_Medias.nom_types_media)\
                            .filter(Types_Media.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Posseder_M.avis_popularite == False)\
                            .distinct(Posseder_M.avis_popularite, Posseder_M.id_projets_medias) \
                            .order_by(Posseder_M.id_projets_medias.desc())
                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo,Posseder_T.note,Posseder_T.favori, Posseder_T.date_ajout)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Posseder_T.avis_popularite == False)\
                            .distinct(Posseder_T.avis_popularite, Posseder_T.id_projets_transmedias)\
                            .order_by(Posseder_T.id_projets_transmedias.desc())
                            # add column "type" to the query
                            transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                            collection_query = union_all(media_query, transmedia_query)
                            collection_query = collection_query.order_by(collection_query.c.posseder_m_date_ajout.desc()).limit(10).offset(numstart)
                            my_collection = session.execute(collection_query).all()
                        elif idfiltre == "sur-note":
                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo,Posseder_M.note,Posseder_M.favori, Posseder_M.date_ajout, Types_Media.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .join(Types_Media, Types_Media.nom_types_media == Projets_Medias.nom_types_media)\
                            .filter(Types_Media.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Posseder_M.avis_cote == True)\
                            .distinct(Posseder_M.avis_cote, Posseder_M.id_projets_medias) \
                            .order_by(Posseder_M.id_projets_medias.desc())
                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo,Posseder_T.note,Posseder_T.favori, Posseder_T.date_ajout)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Posseder_T.avis_cote == True)\
                            .distinct(Posseder_T.avis_cote, Posseder_T.id_projets_transmedias)\
                            .order_by(Posseder_T.id_projets_transmedias.desc())
                            # add column "type" to the query
                            transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                            collection_query = union_all(media_query, transmedia_query)
                            collection_query = collection_query.order_by(collection_query.c.posseder_m_date_ajout.desc()).limit(10).offset(numstart)
                            my_collection = session.execute(collection_query).all()
                        elif idfiltre == "sous-note":
                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo,Posseder_M.note,Posseder_M.favori, Posseder_M.date_ajout, Types_Media.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .join(Types_Media, Types_Media.nom_types_media == Projets_Medias.nom_types_media)\
                            .filter(Types_Media.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Posseder_M.avis_cote == False)\
                            .distinct(Posseder_M.avis_cote, Posseder_M.id_projets_medias) \
                            .order_by(Posseder_M.id_projets_medias.desc())
                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo,Posseder_T.note,Posseder_T.favori, Posseder_T.date_ajout)\
                            .select_from(Posseder_T) \
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches) \
                            .filter(Posseder_T.pseudo == user) \
                            .filter(Posseder_T.avis_cote == False) \
                            .distinct(Posseder_T.avis_cote, Posseder_T.id_projets_transmedias) \
                            .order_by(Posseder_T.id_projets_transmedias.desc())
                            # add column "type" to the query
                            transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                            collection_query = union_all(media_query, transmedia_query)
                            collection_query = collection_query.order_by(collection_query.c.posseder_m_date_ajout.desc()).limit(10).offset(numstart)
                            my_collection = session.execute(collection_query).all()
                        else:
                            return make_response(jsonify({'message': 'filtre inconnu'}), 400)
                        mycollection_reponse = []
                        if not isadulte:
                            my_collection = [c for c in my_collection if c[4] == False]
                        if client == "app":
                            mycollection_reponse.append({'macollection': [{'id': c[0], 'nom': c[1], 'url_image': c[2], 'adulte': c[4]} for c in my_collection]})
                            for i in range(len(mycollection_reponse[0]['macollection'])):
                                mycollection_reponse[0]['macollection'][i]['date-ajout'] = my_collection[i][len(my_collection[i]) - 2] if idfiltre == "" or idfiltre == "date-ajout" else None
                            return make_response(jsonify(mycollection_reponse), 200)
                        else:
                            return my_collection
                    else:
                        return make_response(jsonify({'message': 'filtre inconnu'}), 400)
                else:
                    return make_response(jsonify({'message': 'type inconnu'}), 400)
            else:
                return make_response(jsonify({'message': 'cette valeur doit être un nombre entier'}), 400)
        else:
            return make_response(jsonify({'message': 'le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations'}),400)
    else:
        return make_response(jsonify({'message': 'utilisateur inconnu'}), 400)