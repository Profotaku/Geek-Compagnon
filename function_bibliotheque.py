from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin
from config import *


def bibliotheque_app(session, idtype, idfiltre, numstart):
    #if idtype correspond to a type media in the database
    if type(numstart) == int:
        if session.query(Types_Media).filter_by(nom_types_media=idtype).first() is not None or idtype == "all":
            if idfiltre in ["", "date", "popularite", "note"]:
                bibliotheque = session.execute(select(Produits_Culturels.id_produits_culturels, Fiches.nom, Produits_Culturels.date_sortie, Fiches.url_image, Fiches.id_fiches)\
                    .select_from(Produits_Culturels)\
                    .join(Fiches)\
                    .filter(Produits_Culturels.nom_types_media == Types_Media.nom_types_media) \
                    .filter(Produits_Culturels.id_fiches == Fiches.id_fiches).offset(numstart).limit(10)).all()
                #return name, date, url_image, id_fiche in dict format
                return make_response(jsonify({'bibliotheque': [{'nom': b.nom, 'date': b.date_sortie, 'url_image': b.url_image, 'id_fiche': b.id_fiches} for b in bibliotheque]}), 200)
            else:
                return make_response(jsonify({'message': 'filtre inconnu'}), 400)
        else:
            return make_response(jsonify({'message': 'type inconnu'}), 400)
    else:
        return make_response(jsonify({'message': 'numstart doit être un entier'}), 400)

