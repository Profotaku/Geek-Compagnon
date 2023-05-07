from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal
from config import *
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    verify_jwt_in_request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user


def mybibliotheque_app(session, idtype, idfiltre, numstart, client, user):
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
                    if idfiltre in ["", "date-ajout", "top-note", "favori", "sur-mediatise", "sous-mediatise", "sur-note", "sous-note", "physiquement", "virtuellement", "souhaite", "limite", "collector"]:
                        if type(idtype) != list:
                            idtype = [idtype]
                        if idfiltre == "" or idfiltre == "date-ajout":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Produits_Culturels.verifie == True) \
                                .distinct(Posseder_C.date_ajout, Posseder_C.id_produits_culturels ) \
                                .order_by(Posseder_C.date_ajout.desc()) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "top-note":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Produits_Culturels.verifie == True) \
                                .distinct(Posseder_C.note, Posseder_C.id_produits_culturels ) \
                                .order_by(Posseder_C.note.desc()) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "favori":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.favori == True)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "sur-mediatise":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.avis_popularite == True)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "sous-mediatise":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.avis_popularite == False)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "sur-note":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.avis_cote == True)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "sous-note":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.avis_cote == False)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "physiquement":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.physiquement == True)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "virtuellement":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.physiquement == False)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "souhaite":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.souhaite == True)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "limite":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.limite == True)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()
                        elif idfiltre == "collector":
                            my_bibliotheque = session.execute(select(Fiches.nom, Fiches.url_image, Fiches.id_fiches, Fiches.adulte, Types_Media.nom_types_media, Posseder_C.id_produits_culturels, Posseder_C.pseudo, Posseder_C.date_ajout,Posseder_C.note,Posseder_C.favori, Posseder_C.limite, Posseder_C.collector)\
                                .select_from(Posseder_C)\
                                .join(Produits_Culturels, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels)\
                                .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches)\
                                .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media)\
                                .filter(Types_Media.nom_types_media.in_(idtype))\
                                .filter(Posseder_C.pseudo == user)\
                                .filter(Posseder_C.collector == True)\
                                .filter(Produits_Culturels.verifie == True) \
                                .order_by(Posseder_C.id_produits_culturels.desc()) \
                                .limit(10).offset(numstart)).all()


                        else:
                            return make_response(jsonify({'message': 'filtre inconnu'}), 400)
                        if not isadulte:
                            my_bibliotheque = [b for b in my_bibliotheque if b.adulte == False]
                        if client == "app":
                            return make_response(jsonify({'mabibliotheque': [{'nom': b.nom, 'url_image': b.url_image, 'id': b.id_produits_culturels, 'adulte': b.adulte, 'note': b.note, 'favori': b.favori, 'limite': b.limite, 'collector': b.collector,'date-ajout': b.date_ajout } for b in my_bibliotheque]}), 200)
                        if len(idtype) > 1:
                            idtype = "all"
                        else:
                            idtype = idtype[0]
                        if numstart == 0:
                            return render_template('public/mybibliotheque.html', my_bibliotheque=my_bibliotheque, idtype=idtype, idfiltre=idfiltre, numstart=numstart)
                        else:
                            return render_template('public/infine-scroll-mybibliotheque.html', my_bibliotheque=my_bibliotheque, idtype=idtype, idfiltre=idfiltre, numstart=numstart)
                else:
                    return make_response(jsonify({'message': 'type inconnu'}), 400)
            else:
                return make_response(jsonify({'message': 'cette valeur doit être un nombre entier'}), 400)
        else:
            return make_response(jsonify({'message': 'le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations'}), 400)
    else:
        return make_response(jsonify({'message': 'utilisateur inconnu'}), 400)