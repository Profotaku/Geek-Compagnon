from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal, case, distinct
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
    if session.query(Utilisateurs).filter_by(pseudo=user, desactive=False, verifie=True).first() is not None or user is None:
        if session.query(Utilisateurs.profil_public).filter_by(pseudo=user).first()[0] or (user == current_user.pseudo if current_user.is_authenticated else False) or user == get_jwt_identity():
            if type(numstart) == int:
                if session.query(Types_Media).filter_by(nom_types_media=idtype).first() is not None or idtype == "all":
                    if idtype == "all":
                        idtype = session.execute(select(Types_Media.nom_types_media).select_from(Types_Media).distinct(Types_Media.nom_types_media)).all()
                        idtype = [row[0] for row in idtype]
                    if idfiltre in ["", "date-ajout", "top-note", "favori", "sur-mediatise", "sous-mediatise", "sur-note", "sous-note"]:
                        if type(idtype) != list:
                            idtype = [idtype]

                        sub_query_media_total = session.query(Etre_Compose.id_projets_medias, func.count(distinct(Produits_Culturels.id_produits_culturels)).label('total_produits_culturels'))\
                            .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Etre_Compose.id_produits_culturels)\
                            .group_by(Etre_Compose.id_projets_medias)\
                            .subquery()

                        sub_query_media_possedes = session.query(Posseder_M.id_projets_medias, func.count(distinct(case((Posseder_C.pseudo == user, Posseder_C.id_produits_culturels)))).label('produits_culturels_possedes'))\
                            .select_from(Posseder_M) \
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias) \
                            .join(Etre_Compose, Etre_Compose.id_projets_medias == Projets_Medias.id_projets_medias) \
                            .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Etre_Compose.id_produits_culturels) \
                            .join(Posseder_C, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels) \
                            .filter(Posseder_M.pseudo == user)\
                            .group_by(Posseder_M.id_projets_medias) \
                            .subquery()

                        sub_query_transmedia_total = session.query(Contenir.id_projets_transmedias, func.count(distinct(Projets_Medias.id_projets_medias)).label('total_projets_medias'))\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Contenir.id_projets_medias)\
                            .group_by(Contenir.id_projets_transmedias)\
                            .subquery()

                        sub_query_transmedia_possedes = session.query(Posseder_T.id_projets_transmedias, func.count(distinct(case((Posseder_M.pseudo == user, Posseder_M.id_projets_medias)))).label('projets_medias_possedes'))\
                            .select_from(Posseder_T) \
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .join(Contenir, Contenir.id_projets_transmedias == Projets_Transmedias.id_projets_transmedias) \
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Contenir.id_projets_medias) \
                            .join(Posseder_M, Posseder_M.id_projets_medias == Projets_Medias.id_projets_medias) \
                            .filter(Posseder_T.pseudo == user)\
                            .group_by(Posseder_T.id_projets_transmedias) \
                            .subquery()

                        if idfiltre == "" or idfiltre == "date-ajout":

                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .outerjoin(Notes, and_(Notes.pseudo == Posseder_M.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .outerjoin(Avis, and_(Avis.pseudo == Posseder_M.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Projets_Medias.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user) \
                            .outerjoin(sub_query_media_possedes, sub_query_media_possedes.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .outerjoin(sub_query_media_total, sub_query_media_total.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .distinct(Posseder_M.date_ajout, Posseder_M.id_projets_medias)\
                            .group_by(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media) \
                            .order_by(Posseder_M.date_ajout.desc(), Posseder_M.id_projets_medias.desc())

                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes) \
                            .select_from(Posseder_T) \
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches) \
                            .outerjoin(Notes, and_(Notes.pseudo == Posseder_T.pseudo, Notes.id_fiches == Fiches.id_fiches)) \
                            .outerjoin(Avis, and_(Avis.pseudo == Posseder_T.pseudo, Avis.id_fiches == Fiches.id_fiches)) \
                            .filter(Posseder_T.pseudo == user) \
                            .outerjoin(sub_query_transmedia_possedes, sub_query_transmedia_possedes.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .outerjoin(sub_query_transmedia_total, sub_query_transmedia_total.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .distinct(Posseder_T.date_ajout, Posseder_T.id_projets_transmedias) \
                            .group_by(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes) \
                            .order_by(Posseder_T.date_ajout.desc(), Posseder_T.id_projets_transmedias.desc())

                        elif idfiltre == "top-note":

                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .join(Notes, and_(Notes.pseudo == Posseder_M.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .outerjoin(Avis, and_(Avis.pseudo == Posseder_M.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Projets_Medias.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .outerjoin(sub_query_media_possedes, sub_query_media_possedes.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .outerjoin(sub_query_media_total, sub_query_media_total.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .distinct(Notes.note, Posseder_M.id_projets_medias)\
                            .group_by(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media) \
                            .order_by(Notes.note.desc(), Posseder_M.id_projets_medias.desc())\

                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .join(Notes, and_(Notes.pseudo == Posseder_T.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .outerjoin(Avis, and_(Avis.pseudo == Posseder_T.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Posseder_T.pseudo == user) \
                            .outerjoin(sub_query_transmedia_possedes,sub_query_transmedia_possedes.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .outerjoin(sub_query_transmedia_total, sub_query_transmedia_total.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .distinct(Notes.note, Posseder_T.id_projets_transmedias)\
                            .group_by(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes) \
                            .order_by(Notes.note.desc(), Posseder_T.id_projets_transmedias.desc())\

                        elif idfiltre == "favori":

                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .outerjoin(Notes, and_(Notes.pseudo == Posseder_M.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .join(Avis, and_(Avis.pseudo == Posseder_M.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Projets_Medias.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Avis.favori == True)\
                            .outerjoin(sub_query_media_possedes, sub_query_media_possedes.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .outerjoin(sub_query_media_total, sub_query_media_total.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .distinct(Avis.favori, Posseder_M.id_projets_medias) \
                            .group_by(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media) \
                            .order_by(Posseder_M.id_projets_medias.desc())

                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .outerjoin(Notes, and_(Notes.pseudo == Posseder_T.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .join(Avis, and_(Avis.pseudo == Posseder_T.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Avis.favori == True)\
                            .outerjoin(sub_query_transmedia_possedes, sub_query_transmedia_possedes.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .outerjoin(sub_query_transmedia_total, sub_query_transmedia_total.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .distinct(Avis.favori, Posseder_T.id_projets_transmedias)\
                            .group_by(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes) \
                            .order_by(Posseder_T.id_projets_transmedias.desc())

                        elif idfiltre == "sur-mediatise":

                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .outerjoin(Notes, and_(Notes.pseudo == Posseder_M.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .join(Avis, and_(Avis.pseudo == Posseder_M.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Projets_Medias.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Avis.avis_popularite == 1)\
                            .outerjoin(sub_query_media_possedes, sub_query_media_possedes.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .outerjoin(sub_query_media_total, sub_query_media_total.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .distinct(Avis.avis_popularite, Posseder_M.id_projets_medias) \
                            .group_by(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Avis.avis_popularite, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media) \
                            .order_by(Posseder_M.id_projets_medias.desc())

                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Avis.avis_popularite == 1)\
                            .outerjoin(sub_query_transmedia_possedes, sub_query_transmedia_possedes.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .outerjoin(sub_query_transmedia_total, sub_query_transmedia_total.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .distinct(Avis.avis_popularite, Posseder_T.id_projets_transmedias)\
                            .group_by(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Avis.avis_popularite, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes) \
                            .order_by(Posseder_T.id_projets_transmedias.desc())

                        elif idfiltre == "sous-mediatise":

                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .outerjoin(Notes, and_(Notes.pseudo == Posseder_M.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .join(Avis, and_(Avis.pseudo == Posseder_M.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Projets_Medias.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Avis.avis_popularite == -1)\
                            .outerjoin(sub_query_media_possedes, sub_query_media_possedes.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .outerjoin(sub_query_media_total, sub_query_media_total.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .distinct(Avis.avis_popularite, Posseder_M.id_projets_medias) \
                            .group_by(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Avis.avis_popularite, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media) \
                            .order_by(Posseder_M.id_projets_medias.desc())

                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Avis.avis_popularite == -1)\
                            .outerjoin(sub_query_transmedia_possedes, sub_query_transmedia_possedes.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .outerjoin(sub_query_transmedia_total, sub_query_transmedia_total.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .distinct(Avis.avis_popularite, Posseder_T.id_projets_transmedias)\
                            .group_by(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Avis.avis_popularite, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes) \
                            .order_by(Posseder_T.id_projets_transmedias.desc())

                        elif idfiltre == "sur-note":

                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .outerjoin(Notes, and_(Notes.pseudo == Posseder_M.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .join(Avis, and_(Avis.pseudo == Posseder_M.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Projets_Medias.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Avis.avis_cote == 1)\
                            .outerjoin(sub_query_media_possedes, sub_query_media_possedes.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .outerjoin(sub_query_media_total, sub_query_media_total.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .distinct(Avis.avis_cote, Posseder_M.id_projets_medias) \
                            .group_by(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Avis.avis_cote, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media) \
                            .order_by(Posseder_M.id_projets_medias.desc())

                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Avis.avis_cote == 1)\
                            .outerjoin(sub_query_transmedia_possedes, sub_query_transmedia_possedes.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .outerjoin(sub_query_transmedia_total, sub_query_transmedia_total.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .distinct(Avis.avis_cote, Posseder_T.id_projets_transmedias)\
                            .group_by(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Avis.avis_cote, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes) \
                            .order_by(Posseder_T.id_projets_transmedias.desc())

                        elif idfiltre == "sous-note":

                            media_query = session.query(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media)\
                            .select_from(Posseder_M)\
                            .join(Projets_Medias, Projets_Medias.id_projets_medias == Posseder_M.id_projets_medias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches)\
                            .outerjoin(Notes, and_(Notes.pseudo == Posseder_M.pseudo, Notes.id_fiches == Fiches.id_fiches))\
                            .join(Avis, and_(Avis.pseudo == Posseder_M.pseudo, Avis.id_fiches == Fiches.id_fiches))\
                            .filter(Projets_Medias.nom_types_media.in_(idtype))\
                            .filter(Posseder_M.pseudo == user)\
                            .filter(Avis.avis_cote == -1)\
                            .outerjoin(sub_query_media_possedes, sub_query_media_possedes.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .outerjoin(sub_query_media_total, sub_query_media_total.c.id_projets_medias == Posseder_M.id_projets_medias) \
                            .distinct(Avis.avis_cote, Posseder_M.id_projets_medias) \
                            .group_by(Posseder_M.id_projets_medias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_M.pseudo, Notes.note, Avis.favori, Avis.avis_cote, Posseder_M.date_ajout, sub_query_media_total.c.total_produits_culturels, sub_query_media_possedes.c.produits_culturels_possedes, Projets_Medias.nom_types_media) \
                            .order_by(Posseder_M.id_projets_medias.desc())

                            transmedia_query = session.query(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes)\
                            .select_from(Posseder_T)\
                            .join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias)\
                            .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches)\
                            .filter(Posseder_T.pseudo == user)\
                            .filter(Avis.avis_cote == -1)\
                            .outerjoin(sub_query_transmedia_possedes, sub_query_transmedia_possedes.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .outerjoin(sub_query_transmedia_total, sub_query_transmedia_total.c.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
                            .distinct(Avis.avis_cote, Posseder_T.id_projets_transmedias)\
                            .group_by(Posseder_T.id_projets_transmedias, Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Posseder_T.pseudo, Notes.note, Avis.favori, Avis.avis_cote, Posseder_T.date_ajout, sub_query_transmedia_total.c.total_projets_medias, sub_query_transmedia_possedes.c.projets_medias_possedes) \
                            .order_by(Posseder_T.id_projets_transmedias.desc())

                        else:
                            return make_response(jsonify({'message': 'filtre inconnu'}), 400)
                        # add column "type" to the query
                        transmedia_query = transmedia_query.add_column(literal("all").label("nom_type_media"))
                        collection_query = union_all(media_query, transmedia_query)
                        collection_query = collection_query.order_by(collection_query.c.posseder_m_date_ajout.desc()).limit(10).offset(numstart)
                        my_collection = session.execute(collection_query).all()
                        mycollection_reponse = []
                        if not isadulte:
                            my_collection = [c for c in my_collection if c[4] == False]
                        if client == "app":
                            mycollection_reponse.append({'macollection': [{'id': c[0], 'nom': c[1], 'url_image': c[2], 'adulte': c[4], 'note': c[6] if c[6] is not None else None, 'favori': c[7] if c[7] is not None else False, 'nombre_possession': c[9] if c[9] is not None else 0, 'nombre_total': c[10] if c[10] is not None else 0} for c in my_collection]})
                            for i in range(len(mycollection_reponse[0]['macollection'])):
                                mycollection_reponse[0]['macollection'][i]['date-ajout'] = my_collection[i][len(my_collection[i]) - 4] if idfiltre == "" or idfiltre == "date-ajout" else None
                            return make_response(jsonify(mycollection_reponse), 200)
                        if len(idtype) > 1:
                            idtype = "all"
                        else:
                            idtype = idtype[0]
                        if numstart == 0:
                            return render_template('public/mycollection.html', my_collection=my_collection, idtype=idtype, idfiltre=idfiltre, numstart=numstart)
                        else:
                            return render_template('public/infine-scroll-mycollection.html', my_collection=my_collection, idtype=idtype, idfiltre=idfiltre, numstart=numstart)
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