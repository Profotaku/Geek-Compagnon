from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from dataclass import *
from config import *
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func
from flask_login import current_user
from flask_jwt_extended import get_jwt_identity
import threading

lock = threading.Lock()
def ajouter_fiche_culturel(session):
    nom_input = request.form.get('nom-input')
    synopsis_input = request.form.get('synopsis-input')
    infos_input = request.form.get('infos-input')
    concepteur_input = request.form.get('concepteur-input')
    adulte_checkbox = request.form.get('adulte-checkbox')
    media_type_input = request.form.get('media-type-input')
    current_user_id = None
    if current_user:
        current_user_id = current_user.id_utilisateurs

    if jwt_user_id := get_jwt_identity():
        current_user_id = jwt_user_id

    url_image = request.files['file']

    date_sortie_input = request.form.get('date-sortie-input')

    ean_inputs = [
        value
        for name, value in request.form.items()
        if name.startswith('ean-input-')
    ]

    alternative_names = [
        value
        for name, value in request.form.items()
        if name.startswith('alternative-name-')
    ]

    genres = [
        value
        for name, value in request.form.items()
        if name.startswith('genres-')
    ]

    #create table Avis
    avis = Avis(id_avis=(session.query(func.max(Avis.id_avis)).scalar() or 0)+1, trop_popularite=0, neutre_popularite=0, manque_popularite=0, trop_cote=0, neutre_cote=0, manque_cote=0)
    session.add(avis)
    session.commit()

    #create table Notes
    notes = Notes(id_notes=(session.query(func.max(Notes.id_notes)).scalar() or 0)+1, note_0=0, note_1=0, note_2=0, note_3=0, note_4=0, note_5=0, note_6=0, note_7=0, note_8=0, note_9=0, note_10=0)
    session.add(notes)
    session.commit()

