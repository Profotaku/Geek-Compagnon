from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc
from config import *


def bibliotheque_app(session, idtype, idfiltre, numstart, client):
    if type(numstart) == int:
        isadulte = False
        verify_jwt_in_request(optional=True)
        if current_user.is_authenticated:
            isadulte = current_user.is_adulte
        if get_jwt_identity() is not None:
            isadulte = session.execute(select(Utilisateurs.adulte).where(Utilisateurs.pseudo == get_jwt_identity())).scalar()
        # if idtype correspond to a type media in the database
        if session.query(Types_Media).filter_by(nom_types_media=idtype).first() is not None or idtype == "all":
            if idtype == "all":
                idtype = session.execute(select(Types_Media.nom_types_media).select_from(Types_Media).distinct(Types_Media.nom_types_media)).all()
                idtype = [row[0] for row in idtype]
            if idfiltre in ["", "date-ajout", "date-sortie", "top-consultation", "top-note", "top-favoris", "sur-mediatise", "sous-mediatise", "sur-note", "sous-note"]:
                #transform idtype into a list for the query compatibility (based on filter all)
                if type(idtype) != list:
                    idtype = [idtype]
                if idfiltre == "" or idfiltre == "date-ajout":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte)\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .distinct(Produits_Culturels.id_produits_culturels)\
                        .order_by(Produits_Culturels.id_produits_culturels.desc())\
                        .limit(10).offset(numstart))\
                        .all()
                elif idfiltre == "date-sortie":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte)\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Produits_Culturels.date_sortie.desc())\
                        .limit(10).offset(numstart))\
                        .all()
                elif idfiltre == "top-consultation":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Fiches.consultation)\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Fiches.consultation.desc())\
                        .limit(10).offset(numstart))\
                        .all()
                elif idfiltre == "top-note":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, Notes.note_0,  Notes.note_1, Notes.note_2, Notes.note_3, Notes.note_4, Notes.note_5, Notes.note_6, Notes.note_7, Notes.note_8, Notes.note_9, Notes.note_10, func.avg((Notes.note_0 + Notes.note_1 + Notes.note_2 + Notes.note_3 + Notes.note_4 + Notes.note_5 + Notes.note_6 + Notes.note_7 + Notes.note_8 + Notes.note_9 + Notes.note_10)/11).label('moyenne_notes'))\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Produits_Culturels.id_notes == Notes.id_notes) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .group_by(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Notes.id_notes, Notes.note_0, Notes.note_1, Notes.note_2, Notes.note_3, Notes.note_4, Notes.note_5, Notes.note_6, Notes.note_7, Notes.note_8, Notes.note_9, Notes.note_10)\
                        .order_by(desc('moyenne_notes'))\
                        .limit(10).offset(numstart))\
                        .all()
                elif idfiltre == "top-favoris":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Fiches.cmpt_favori)\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Fiches.cmpt_favori.desc())\
                        .limit(10).offset(numstart))\
                        .all()
                elif idfiltre == "sur-mediatise":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.trop_popularite)\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Produits_Culturels.id_avis == Avis.id_avis) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Avis.trop_popularite.desc())\
                        .limit(10).offset(numstart))\
                        .all()
                elif idfiltre == "sous-mediatise":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.manque_popularite)\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Produits_Culturels.id_avis == Avis.id_avis) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Avis.manque_popularite.desc())\
                        .limit(10).offset(numstart))\
                        .all()
                elif idfiltre == "sur-note":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.trop_cote)\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Produits_Culturels.id_avis == Avis.id_avis) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Avis.trop_cote.desc())\
                        .limit(10).offset(numstart))\
                        .all()
                elif idfiltre == "sous-note":
                    bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Avis.manque_cote)\
                        .select_from(Produits_Culturels)\
                        .join(Types_Media)\
                        .filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
                        .filter(Produits_Culturels.verifie == True) \
                        .filter(Produits_Culturels.id_avis == Avis.id_avis) \
                        .filter(Types_Media.nom_types_media.in_(idtype)) \
                        .order_by(Avis.manque_cote.desc())\
                        .limit(10).offset(numstart))\
                        .all()
                else:
                    return make_response(jsonify({'message': 'filtre inconnu'}), 400)
                if isadulte:
                    bibliotheque = [b for b in bibliotheque if b.adulte == False]
                if client == "app":
                    return make_response(jsonify({'bibliotheque': [{'nom': b.nom, 'date': b.date_sortie, 'url_image': b.url_image, 'id': b.id_produits_culturels, 'adulte': b.adulte, 'consultation': b.consultation if idfiltre == "top-consultation" else None, 'note': round(b.moyenne_notes, 2) if idfiltre == "top-note" else None, 'favoris': b.cmpt_favori if idfiltre == 'top-favoris' else None, 'sur-mediatise': b.trop_popularite if idfiltre == 'sur-mediatise' else None, 'sous-mediatise' : b.manque_popularite if idfiltre == 'sous-mediatise' else None, 'sur-note': b.trop_cote if idfiltre == 'sur-note' else None, 'sous-note': b.manque_cote if idfiltre == 'sous-note' else None} for b in bibliotheque]}), 200)
                else:
                    return bibliotheque
            else:
                return make_response(jsonify({'message': 'filtre inconnu'}), 400)
        else:
            return make_response(jsonify({'message': 'type inconnu'}), 400)
    else:
        return make_response(jsonify({'message': 'cette valeur doit être un nombre entier'}), 400)

