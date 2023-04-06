from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
from config import *


def bibliotheque_app(session, idtype, idfiltre, numstart):
    #if idtype correspond to a type media in the database
    if session.query(Types_Media).filter_by(nom_types_media=idtype).first() is not None or idtype == "all":
        if idfiltre in ["", "date", "popularite", "note"]:
            if numstart.isdigit():
                bibliotheque = session.query(Produits_Culturels).filter_by(id_types_media=idtype).order_by(Produits_Culturels.date_creation.desc()).limit(10).offset(numstart)
                #return name, date, url_image, id_fiche in dict format
                return make_response(jsonify({'bibliotheque': [{'nom': b.nom, 'date': b.date_creation, 'url_image': b.url_image, 'id_fiche': b.id_fiches} for b in bibliotheque]}), 200)
            else:
                return make_response(jsonify({'message': 'start must be a number'}), 400)
        else:
            return make_response(jsonify({'message': 'filtre inconnu'}), 400)
    else:
        return make_response(jsonify({'message': 'type inconnu'}), 400)

