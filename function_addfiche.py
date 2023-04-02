from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
from config import *
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func
from flask_login import current_user
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
def ajouter_fiche_culturel(session):
    nom_input = request.form.get('nom-input')
    synopsis_input = request.form.get('synopsis-input')
    infos_input = request.form.get('infos-input')
    concepteur_input = request.form.get('concepteur-input')
    adulte_checkbox = request.form.get('adulte-checkbox')
    media_type_input = request.form.get('media-type-input')
    current_user_id = None
    if current_user.is_authenticated:
        current_user_id = current_user.id_utilisateurs



    url_image = request.files['file']

    date_sortie_input = request.form.get('date-sortie-input')

    ean_inputs = []

    # boucle sur chaque champ de saisie dans le formulaire
    for name, value in request.form.items():
        # vérifie si le champ commence par "ean-input-"
        if name.startswith('ean-input-'):
            # vérifie si la valeur saisie correspond à un code EAN-13 ou à un code ISBN-13
            if len(value) == 13 and value.isdigit():
                # la valeur saisie correspond à un code EAN-13 valide
                ean = value
            elif len(value) == 9 and value.isdigit():
                # la valeur saisie correspond à un code ISBN-10 valide
                isbn_prefix = '978'
                isbn = isbn_prefix + value

                # conversion de l'ISBN-10 en ISBN-13
                digits = [int(d) for d in isbn]
                factor = [1, 3] * 6
                sum_ = sum([d * f for d, f in zip(digits, factor)])
                check_digit = (10 - (sum_ % 10)) % 10
                ean = isbn + str(check_digit)
            else:
                # la valeur saisie n'est pas un code EAN-13 ni un code ISBN-13 valide
                print(f"Erreur : la valeur {value} n'est pas un code EAN-13 ni un code ISBN-13 valide.")
                continue

            # extrait les 12 premiers chiffres du code EAN-13
            ean_digits = [int(d) for d in ean[:-1]]

            # calcul de la somme de contrôle
            sum_ = sum(ean_digits[::2]) + sum(ean_digits[1::2]) * 3
            check_digit = (10 - (sum_ % 10)) % 10

            # vérification de la somme de contrôle
            if check_digit != int(ean[-1]):
                # si la somme de contrôle ne correspond pas, affiche un message d'erreur
                print(f"Erreur : la somme de contrôle pour {ean} est incorrecte.")
            else:
                # sinon, ajoute le code EAN-13 dans la liste
                ean_inputs.append(ean)

    alternative_names = [
        value
        for name, value in request.form.items()
        if name.startswith('alternative-name-')
    ]

    genres = []

    for name, value in request.form.items():
        if (
            name.startswith('genre-')
            and value not in genres
            and value is not None
        ):
            # vérifie si le genre existe déjà dans la base de données
            genre = session.query(Etre_Associe).filter(Etre_Associe.nom_genres == value, Etre_Associe.nom_types_media == media_type_input).first()
            if genre is not None:
                # si le genre existe déjà, ajoute l'identifiant du genre dans la liste
                genres.append(value)

    session.close()
    insertion = session.begin()

    try:
        #create table Avis
        avis = Avis(id_avis=(session.query(func.max(Avis.id_avis)).scalar() or 0)+1, trop_popularite=0, neutre_popularite=0, manque_popularite=0, trop_cote=0, neutre_cote=0, manque_cote=0)
        session.add(avis)
        session.commit()

        #create table Notes
        notes = Notes(id_notes=(session.query(func.max(Notes.id_notes)).scalar() or 0)+1, note_0=0, note_1=0, note_2=0, note_3=0, note_4=0, note_5=0, note_6=0, note_7=0, note_8=0, note_9=0, note_10=0)
        session.add(notes)
        session.commit()

        #create tables EAN13
        for ean_input in ean_inputs:
            #check if ean already exist and not in the table
            if ean_input != "" and session.query(EAN13).filter(EAN13.ean13 == ean_input).first() is None:
                ean = EAN13(ean13=ean_input, limite=False, collector=False)
                session.add(ean)
                session.commit()

        #create tables Noms_Alternatifs
        for alternative_name in alternative_names:
            #check if alternative name already exist and not in the table
            if alternative_name != "" and session.query(Noms_Alternatifs).filter(Noms_Alternatifs.nom_alternatif == alternative_name).first() is None:
                nom_alternatif = Noms_Alternatifs(nom_alternatif=alternative_name)
                session.add(nom_alternatif)
                session.commit()

        #create table Fiche
        fiche = Fiches(id_fiches=(session.query(func.max(Fiches.id_fiches)).scalar() or 0)+1, nom=nom_input, synopsis=synopsis_input, cmpt_note=0, moy_note=0, cmpt_favori=0, consultation=0, contributeur=current_user_id, adulte=adulte_checkbox, info=infos_input, concepteur=concepteur_input)
        session.add(fiche)
        session.commit()

        #create table Produits_Culturels
        produit_culturel = Produits_Culturels(id_produits_culturels=(session.query(func.max(Produits_Culturels.id_produits_culturels)).scalar() or 0)+1, date_sortie=date_sortie_input, id_notes=notes.id_notes, id_avis=avis.id_avis, nom_types_media=media_type_input, id_fiches=fiche.id_fiches)
        session.add(produit_culturel)
        session.commit()

        #crete tables Nommer_C
        for alternative_name in alternative_names:
            nommer_c = Nommer_C(id_produits_culturels=produit_culturel.id_produits_culturels, nom_alternatif=alternative_name)
            session.add(nommer_c)
            session.commit()

        #create tables Etre_Defini
        for genre in genres:
            etre_defini = Etre_Defini(id_produits_culturels=produit_culturel.id_produits_culturels, nom_genres=genre)
            session.add(etre_defini)
            session.commit()

        #crete tables Etre_Identifie

        for ean_input in ean_inputs:
            etre_identifie = Etre_Identifie(id_produits_culturels=produit_culturel.id_produits_culturels, ean13=ean_input)
            session.add(etre_identifie)
            session.commit()


    except:
        # En cas d'erreur, annulez la transaction
        insertion.rollback()
        raise
    finally:
        # Fermez la session
        session.close()

    return make_response(jsonify({'message': 'Tout marche bien'}), 200)




