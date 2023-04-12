
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from dataclass import *
import re
import os
from config import *
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func
from flask_login import current_user
from success_icon import stylize_image
def ajouter_fiche_culturel(session):
    nom_input = request.form.get('nom-input') if request.form.get('nom-input') != "" else None
    synopsis_input = request.form.get('synopsis-input') if request.form.get('synopsis-input') != "" else None
    infos_input = request.form.get('infos-input') if request.form.get('infos-input') != "" else None
    concepteur_input = request.form.get('concepteur-input') if request.form.get('concepteur-input') != "" else None
    adulte_checkbox = bool(request.form.get('adulte-checkbox'))
    media_type_input = request.form.get('media-type-input') if request.form.get('media-type-input') != "" else None
    current_user_id = None
    if current_user.is_authenticated:
        current_user_id = current_user.id_utilisateurs

    #check if nom_input is None
    if nom_input is None:
        return make_response(jsonify({'message': "Le nom de la fiche n'est pas saisie" }), 400)

    #check if media_type_input is in database
    if media_type_input is not None:
        media_type = session.query(Types_Media).filter_by(nom_types_media=media_type_input).first()
        if media_type is None:
            return make_response(jsonify({'message': "Le type de média n'est pas dans la base de données" }), 400)
    else:
        return make_response(jsonify({'message': "Le type de média n'est pas saisie" }), 400)


    #check if request file exist
    if 'dropz-visual' in request.files:
        url_image = request.files['dropz-visual']
        file_signature = url_image.read(8)
        #check signature of file detect if it's png or jpg
        if not file_signature.startswith(Image_Signature.JPEG) and not file_signature.startswith(Image_Signature.PNG):
            return make_response(jsonify({'message': "Le fichier n'est pas une image dans un format accepté" }), 400)
        if file_signature.startswith(Image_Signature.PNG):
            #convert png to jpg
            url_image = Image.open(url_image)
            url_image = url_image.convert('RGB')
        elif file_signature.startswith(Image_Signature.JPEG):
            url_image = Image.open(url_image)

        # check if image dimension is correct
        if url_image.height < 300 or url_image.width < 300:
            return make_response(jsonify({'message': "L'image est trop petite, elle doit faire au minimum 300x300 pixels" }), 400)

    date_sortie_input = request.form.get('date-sortie-input')

    if date_sortie_input == '':
        date_sortie_input = None

    is_limited_inputs = [
        value
        for name, value in request.form.items()
        if name.startswith('is-limited-input-')
    ]
    is_collector_inputs = [
        value
        for name, value in request.form.items()
        if name.startswith('is-collector-input-')
    ]
    ean_inputs = []

    # boucle sur chaque champ de saisie dans le formulaire
    for name, value in request.form.items():
        # vérifie si le champ commence par "ean-input-"
        if name.startswith('ean-input-'):
            # delete dashes in ean if exist
            value = value.replace('-', '')
            # vérifie si la valeur saisie correspond à un code EAN-13 ou à un code ISBN-13
            if len(value) == 13 and value.isdigit():
                # la valeur saisie correspond à un code EAN-13 valide
                ean = value
            elif len(value) == 10 and value.isdigit():

                isbn = f'978{value}'

                # conversion de l'ISBN-10 en ISBN-13
                digits = [int(d) for d in isbn]
                factor = [1, 3] * 6
                sum_ = sum(d * f for d, f in zip(digits, factor))
                check_digit = (10 - (sum_ % 10)) % 10
                ean = isbn + str(check_digit)
            elif value == '':
                continue
            else:
                # la valeur saisie n'est pas un code EAN-13 ni un code ISBN-13 valide
                return make_response(
                    jsonify({'message': f"Le code EAN-13 ayant pour valeur {value}n'est pas d'une longueur valide."}), 400)


            # extrait les 12 premiers chiffres du code EAN-13
            ean_digits = [int(d) for d in ean[:-1]]

            # calcul de la somme de contrôle
            sum_ = sum(ean_digits[::2]) + sum(ean_digits[1::2]) * 3
            check_digit = (10 - (sum_ % 10)) % 10

            if check_digit != int(ean[-1]):
                # si la somme de contrôle ne correspond pas, affiche un message d'erreur
                return make_response(
                    jsonify({'message': f'Le code EAN-13 ayant pour valeur {ean} est invalide.'}), 400,)
            # sinon, ajoute le code EAN-13 dans la liste
            #get number in name
            number = re.search(r'\d+', name).group()
            #add in ean list ean and is_limited and is_collector
            ean_inputs.append([ean, is_limited_inputs[int(number)], is_collector_inputs[int(number)]])

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
            else:
                # si le genre n'existe pas, make response
                return make_response(jsonify({'message': f"Le genre {value} n'existe pas dans la base de données ou n'est pas associé à ce type de média" }), 400)


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
            if ean_input[0] != "" and session.query(EAN13).filter(EAN13.ean13 == ean_input[0]).first() is None:
                ean = EAN13(ean13=ean_input[0], limite=bool(ean_input[1]), collector=bool(ean_input[2]))
                session.add(ean)
                session.commit()

        #create tables Noms_Alternatifs
        for alternative_name in alternative_names:
            #check if alternative name already exist and not in the table
            if alternative_name != "" and session.query(Noms_Alternatifs).filter(Noms_Alternatifs.nom_alternatif == alternative_name).first() is None:
                nom_alternatif = Noms_Alternatifs(nom_alternatif=alternative_name)
                session.add(nom_alternatif)
                session.commit()

        #crete sub folder in /static/images/fiches/ in function of the id of the fiche
        id_fiche = (session.query(func.max(Fiches.id_fiches)).scalar() or 0)+1
        #check if folder exist
        if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche))):
            os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche)))
        relative_path = None
        #save image in the relative folder
        if 'dropz-visual' in request.files:
            url_image.seek(0)
            url_image.save(os.path.join(f'static/images/fiches/{str(id_fiche)}/', "visual.jpg"))
            #open image for optimization
            saved_image = Image.open(f'static/images/fiches/{str(id_fiche)}/visual.jpg')
            #save in same path with optimization
            wpercent = (460 / float(saved_image.size[0]))
            hsize = int((float(saved_image.size[1]) * float(wpercent)))
            saved_image.thumbnail((460, hsize), Image.LANCZOS)
            saved_image.save(f'static/images/fiches/{str(id_fiche)}/visual.jpg', optimize=True, quality=95, progressive=True)
            relative_path = os.path.join('static/images/fiches/', str(id_fiche), "visual.jpg")

        #create table Fiche
        fiche = Fiches(id_fiches=(session.query(func.max(Fiches.id_fiches)).scalar() or 0)+1, nom=nom_input, synopsis=synopsis_input, cmpt_note=0, moy_note=0, cmpt_favori=0, consultation=0, contributeur=current_user_id, adulte=adulte_checkbox, info=infos_input, concepteur=concepteur_input, url_image=relative_path)
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
        print(Exception)
        make_response(jsonify({'message': 'Les données saisie semble être invalides, veuillez les vérifier. Contacter un administrateur si besoin'}), 400)
    finally:
        # Fermez la session
        session.close()

    return make_response(jsonify({'message': 'Tout marche bien'}), 200)







def ajouter_fiche_media(session):
    nom_input = request.form.get('nom-input') if request.form.get('nom-input') != "" else None
    synopsis_input = request.form.get('synopsis-input') if request.form.get('synopsis-input') != "" else None
    infos_input = request.form.get('infos-input') if request.form.get('infos-input') != "" else None
    concepteur_input = request.form.get('concepteur-input') if request.form.get('concepteur-input') != "" else None
    adulte_checkbox = bool(request.form.get('adulte-checkbox'))
    media_type_input = request.form.get('media-type-input') if request.form.get('media-type-input') != "" else None
    titre_input = request.form.get('titre-input') if request.form.get('titre-input') != "" else None
    description_input = request.form.get('description-input') if request.form.get('description-input') != "" else None

    current_user_id = None
    if current_user.is_authenticated:
        current_user_id = current_user.id_utilisateurs

    #check if nom_input is None
    if nom_input is None:
        return make_response(jsonify({'message': "Le nom de la fiche n'est pas saisie" }), 400)

    if session.query(Succes).filter_by(titre=titre_input).first() is not None:
        return make_response(jsonify({'message': "Le titre du succès est déjà utilisé, et nous souhaitons garder une certaine originalité dans les succès! Faites parler votre imagination!" }), 400)

    #check if synopsis_input is None ou ""
    if (description_input is None and (titre_input is not None or titre_input == "")) or (description_input == "" and (titre_input is not None or titre_input == "")):
        return make_response(jsonify({'message': "La description du succès n'est pas saisie" }), 400)

    #check if titre_input is None ou ""
    if (titre_input is None and (description_input is not None or description_input == "")) or (titre_input == "" and (description_input is not None or description_input == "")):
        return make_response(jsonify({'message': "Le titre du succès n'est pas saisie" }), 400)

    #check if media_type_input is in database
    if media_type_input is not None:
        media_type = session.query(Types_Media).filter_by(nom_types_media=media_type_input).first()
        if media_type is None:
            return make_response(jsonify({'message': "Le type de média n'est pas dans la base de données" }), 400)
    else:
        return make_response(jsonify({'message': "Le type de média n'est pas saisie" }), 400)

    id_fiche = (session.query(func.max(Fiches.id_fiches)).scalar() or 0) + 1
    if 'dropz-visual' in request.files:
        url_image = request.files['dropz-visual']
        file_signature = url_image.read(8)
        #check signature of file detect if it's png or jpg
        if not file_signature.startswith(Image_Signature.JPEG) and not file_signature.startswith(Image_Signature.PNG):
            return make_response(jsonify({'message': "Le fichier n'est pas une image dans un format accepté" }), 400)
        if file_signature.startswith(Image_Signature.PNG):
            #convert png to jpg
            url_image = Image.open(url_image)
            url_image = url_image.convert('RGB')
        elif file_signature.startswith(Image_Signature.JPEG):
            url_image = Image.open(url_image)
        # check if folder exist
        if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche))):
            os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche)))
        #check if image dimension is correct
        if url_image.height < 300 or url_image.width < 300:
            return make_response(jsonify({'message': "L'image est trop petite, elle doit faire au minimum 300x300 pixels" }), 400)
        # save image in the relative folder
        url_image.seek(0)
        url_image.save(os.path.join(f'static/images/fiches/{str(id_fiche)}/', "visual.jpg"))
        # open image for optimization
        saved_image = Image.open(f'static/images/fiches/{str(id_fiche)}/visual.jpg')
        # save in same path with optimization
        wpercent = (460 / float(saved_image.size[0]))
        hsize = int((float(saved_image.size[1]) * float(wpercent)))
        saved_image.thumbnail((460, hsize), Image.LANCZOS)
        saved_image.save(f'static/images/fiches/{str(id_fiche)}/visual.jpg', optimize=True, quality=95, progressive=True)

    if 'dropz-success' in request.files and titre_input is not None and description_input is not None:
        url_image = request.files['dropz-success']
        file_signature = url_image.read(8)
        #check signature of file detect if it's png or jpg
        if not file_signature.startswith(Image_Signature.JPEG) and not file_signature.startswith(Image_Signature.PNG):
            return make_response(jsonify({'message': "Le fichier n'est pas une image dans un format accepté" }), 400)
        if file_signature.startswith(Image_Signature.PNG):
            #convert png to jpg
            url_image = Image.open(url_image)
            url_image = url_image.convert('RGB')
        elif file_signature.startswith(Image_Signature.JPEG):
            url_image = Image.open(url_image)
        # check if folder exist
        if not os.path.exists(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche))):
            os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche)))
        #check if image dimension is correct
        if url_image.height < 300 or url_image.width < 300:
            return make_response(jsonify({'message': "L'image est trop petite, elle doit faire au minimum 300x300 pixels" }), 400)
        # save image in the relative folder
        url_image.seek(0)
        url_image.save(os.path.join(f'static/images/fiches/{str(id_fiche)}/', "success.jpg"))
        # open image for optimization
        saved_image = Image.open(f'static/images/fiches/{str(id_fiche)}/success.jpg')
        # save in same path with optimization
        wpercent = (460 / float(saved_image.size[0]))
        hsize = int((float(saved_image.size[1]) * float(wpercent)))
        saved_image.thumbnail((460, hsize), Image.LANCZOS)
        saved_image.save(f'static/images/fiches/{str(id_fiche)}/success.jpg', optimize=True, quality=95, progressive=True)
        stylize_image(id_fiche)
    elif 'dropz-success' in request.files and (titre_input is None or description_input is None):
        return make_response(jsonify({'message': "Une icône pour le succès a été transmise mais pas le titre ou la description associé" }), 400)


    alternative_names = [
        value
        for name, value in request.form.items()
        if name.startswith('alternative-name-')
    ]


    session.close()
    insertion = session.begin()
    try:
        # create table Avis
        avis = Avis(id_avis=(session.query(func.max(Avis.id_avis)).scalar() or 0) + 1, trop_popularite=0,
                    neutre_popularite=0, manque_popularite=0, trop_cote=0, neutre_cote=0, manque_cote=0)
        session.add(avis)
        session.commit()

        # create table Notes
        notes = Notes(id_notes=(session.query(func.max(Notes.id_notes)).scalar() or 0) + 1, note_0=0, note_1=0,
                      note_2=0, note_3=0, note_4=0, note_5=0, note_6=0, note_7=0, note_8=0, note_9=0, note_10=0)
        session.add(notes)
        session.commit()

        # create tables Noms_Alternatifs
        for alternative_name in alternative_names:
            # check if alternative name already exist and not in the table
            if alternative_name != "" and session.query(Noms_Alternatifs).filter(
                    Noms_Alternatifs.nom_alternatif == alternative_name).first() is None:
                nom_alternatif = Noms_Alternatifs(nom_alternatif=alternative_name)
                session.add(nom_alternatif)
                session.commit()
        #get the relative path of the image if exist
        relative_path_fiche = os.path.join('static/images/fiches/', str(id_fiche), "visual.jpg") if os.path.isfile('static/images/fiches/'+ str(id_fiche)+"/visual.jpg") else None
        #create table Fiche
        fiche = Fiches(id_fiches=(session.query(func.max(Fiches.id_fiches)).scalar() or 0) + 1, nom=nom_input,
                       synopsis=synopsis_input, cmpt_note=0, moy_note=0, cmpt_favori=0, consultation=0,
                       contributeur=current_user_id, adulte=adulte_checkbox, info=infos_input,
                       concepteur=concepteur_input, url_image=relative_path_fiche)
        session.add(fiche)
        session.commit()

        relative_path_succes = os.path.join('static/images/fiches/', str(id_fiche), "success.jpg") if os.path.isfile('static/images/fiches/'+ str(id_fiche)+"/success.jpg") else None
        # create table Succes if title and description are not empty
        if titre_input is not None and description_input is not None:
            succes = Succes(titre=titre_input, description=description_input, url_image=relative_path_succes)
            session.add(succes)
            session.commit()

        #create table Projets_Medias
        #if succes is not referenced
        if titre_input is None or description_input is None:
            projet_media = Projets_Medias(id_projets_medias=(session.query(func.max(Projets_Medias.id_projets_medias)).scalar() or 0) + 1, id_fiches=fiche.id_fiches, id_notes=notes.id_notes, id_avis=avis.id_avis, titre=None, nom_types_media=media_type_input)
            session.add(projet_media)
            session.commit()
        else:
            projet_media = Projets_Medias(id_projets_medias=(session.query(func.max(Projets_Medias.id_projets_medias)).scalar() or 0) + 1, id_fiches=fiche.id_fiches, id_notes=notes.id_notes, id_avis=avis.id_avis, titre=succes.titre, nom_types_media=media_type_input)
            session.add(projet_media)
            session.commit()

        # create table Nommer_M
        for alternative_name in alternative_names:
            if alternative_name != "":
                nommer_m = Nommer_M(id_projets_medias=projet_media.id_projets_medias,
                                    nom_alternatif=session.query(Noms_Alternatifs).filter(
                                        Noms_Alternatifs.nom_alternatif == alternative_name).first().nom_alternatif)
                session.add(nommer_m)
                session.commit()

    except:
        # En cas d'erreur, annulez la transaction
        insertion.rollback()
        print(Exception)
        make_response(jsonify({'message': 'Les données saisie semble être invalides, veuillez les vérifier. Contacter un administrateur si besoin'}), 400)
    finally:
        # Fermer la session
        session.close()

    return make_response(jsonify({'message': "Tout marche bien" }), 200)


def ajouter_fiche_transmedia(session):
    nom_input = request.form.get('nom-input') if request.form.get('nom-input') != "" else None
    synopsis_input = request.form.get('synopsis-input') if request.form.get('synopsis-input') != "" else None
    infos_input = request.form.get('infos-input') if request.form.get('infos-input') != "" else None
    concepteur_input = request.form.get('concepteur-input') if request.form.get('concepteur-input') != "" else None
    adulte_checkbox = bool(request.form.get('adulte-checkbox'))
    titre_input = request.form.get('titre-input') if request.form.get('titre-input') != "" else None
    description_input = request.form.get('description-input') if request.form.get('description-input') != "" else None

    current_user_id = None
    if current_user.is_authenticated:
        current_user_id = current_user.id_utilisateurs

    #check if nom_input is None
    if nom_input is None:
        return make_response(jsonify({'message': "Le nom de la fiche n'est pas saisie" }), 400)

    if session.query(Succes).filter_by(titre=titre_input).first() is not None:
        return make_response(jsonify({'message': "Le titre du succès est déjà utilisé, et nous souhaitons garder une certaine originalité dans les succès! Faites parler votre imagination!" }), 400)

    #check if synopsis_input is None ou ""
    if (description_input is None and (titre_input is not None or titre_input == "")) or (description_input == "" and (titre_input is not None or titre_input == "")):
        return make_response(jsonify({'message': "La description du succès n'est pas saisie" }), 400)

    #check if titre_input is None ou ""
    if (titre_input is None and (description_input is not None or description_input == "")) or (titre_input == "" and (description_input is not None or description_input == "")):
        return make_response(jsonify({'message': "Le titre du succès n'est pas saisie" }), 400)

    id_fiche = (session.query(func.max(Fiches.id_fiches)).scalar() or 0) + 1
    if 'dropz-visual' in request.files:
        url_image = request.files['dropz-visual']
        file_signature = url_image.read(8)
        #check signature of file detect if it's png or jpg
        if not file_signature.startswith(Image_Signature.JPEG) and not file_signature.startswith(Image_Signature.PNG):
            return make_response(jsonify({'message': "Le fichier n'est pas une image dans un format accepté" }), 400)
        if file_signature.startswith(Image_Signature.PNG):
            #convert png to jpg
            url_image = Image.open(url_image)
            url_image = url_image.convert('RGB')
        elif file_signature.startswith(Image_Signature.JPEG):
            url_image = Image.open(url_image)
        # check if folder exist
        if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche))):
            os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche)))
        #check if image dimension is correct
        if url_image.height < 300 or url_image.width < 300:
            return make_response(jsonify({'message': "L'image est trop petite, elle doit faire au minimum 300x300 pixels" }), 400)
        # save image in the relative folder
        url_image.seek(0)
        url_image.save(os.path.join(f'static/images/fiches/{str(id_fiche)}/', "visual.jpg"))
        # open image for optimization
        saved_image = Image.open(f'static/images/fiches/{str(id_fiche)}/visual.jpg')
        # save in same path with optimization
        wpercent = (460 / float(saved_image.size[0]))
        hsize = int((float(saved_image.size[1]) * float(wpercent)))
        saved_image.thumbnail((460, hsize), Image.LANCZOS)
        saved_image.save(f'static/images/fiches/{str(id_fiche)}/visual.jpg', optimize=True, quality=95, progressive=True)

    if 'dropz-success' in request.files and titre_input is not None and description_input is not None:
        url_image = request.files['dropz-success']
        file_signature = url_image.read(8)
        #check signature of file detect if it's png or jpg
        if not file_signature.startswith(Image_Signature.JPEG) and not file_signature.startswith(Image_Signature.PNG):
            return make_response(jsonify({'message': "Le fichier n'est pas une image dans un format accepté" }), 400)
        if file_signature.startswith(Image_Signature.PNG):
            #convert png to jpg
            url_image = Image.open(url_image)
            url_image = url_image.convert('RGB')
        elif file_signature.startswith(Image_Signature.JPEG):
            url_image = Image.open(url_image)
        # check if folder exist
        if not os.path.exists(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche))):
            os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/fiches/', str(id_fiche)))
        #check if image dimension is correct
        if url_image.height < 300 or url_image.width < 300:
            return make_response(jsonify({'message': "L'image est trop petite, elle doit faire au minimum 300x300 pixels" }), 400)
        # save image in the relative folder
        url_image.seek(0)
        url_image.save(os.path.join(f'static/images/fiches/{str(id_fiche)}/', "success.jpg"))
        # open image for optimization
        saved_image = Image.open(f'static/images/fiches/{str(id_fiche)}/success.jpg')
        # save in same path with optimization
        wpercent = (460 / float(saved_image.size[0]))
        hsize = int((float(saved_image.size[1]) * float(wpercent)))
        saved_image.thumbnail((460, hsize), Image.LANCZOS)
        saved_image.save(f'static/images/fiches/{str(id_fiche)}/success.jpg', optimize=True, quality=95, progressive=True)
        stylize_image(id_fiche)
    elif 'dropz-success' in request.files and (titre_input is None or description_input is None):
        return make_response(jsonify({'message': "Une icône pour le succès a été transmise mais pas le titre ou la description associé" }), 400)


    alternative_names = [
        value
        for name, value in request.form.items()
        if name.startswith('alternative-name-')
    ]


    session.close()
    insertion = session.begin()

    try:
        # create table Avis
        avis = Avis(id_avis=(session.query(func.max(Avis.id_avis)).scalar() or 0) + 1, trop_popularite=0,
                    neutre_popularite=0, manque_popularite=0, trop_cote=0, neutre_cote=0, manque_cote=0)
        session.add(avis)
        session.commit()

        # create table Notes
        notes = Notes(id_notes=(session.query(func.max(Notes.id_notes)).scalar() or 0) + 1, note_0=0, note_1=0,
                      note_2=0, note_3=0, note_4=0, note_5=0, note_6=0, note_7=0, note_8=0, note_9=0, note_10=0)
        session.add(notes)
        session.commit()

        # create tables Noms_Alternatifs
        for alternative_name in alternative_names:
            # check if alternative name already exist and not in the table
            if alternative_name != "" and session.query(Noms_Alternatifs).filter(
                    Noms_Alternatifs.nom_alternatif == alternative_name).first() is None:
                nom_alternatif = Noms_Alternatifs(nom_alternatif=alternative_name)
                session.add(nom_alternatif)
                session.commit()
        #get the relative path of the image if exist
        relative_path_fiche = os.path.join('static/images/fiches/', str(id_fiche), "visual.jpg") if os.path.isfile('static/images/fiches/'+ str(id_fiche)+"/visual.jpg") else None
        #create table Fiche
        fiche = Fiches(id_fiches=(session.query(func.max(Fiches.id_fiches)).scalar() or 0) + 1, nom=nom_input,
                       synopsis=synopsis_input, cmpt_note=0, moy_note=0, cmpt_favori=0, consultation=0,
                       contributeur=current_user_id, adulte=adulte_checkbox, info=infos_input,
                       concepteur=concepteur_input, url_image=relative_path_fiche)
        session.add(fiche)
        session.commit()

        relative_path_succes = os.path.join('static/images/fiches/', str(id_fiche), "success.jpg") if os.path.isfile('static/images/fiches/'+ str(id_fiche)+"/success.jpg") else None
        # create table Succes if title and description are not empty
        if titre_input is not None and description_input is not None:
            succes = Succes(titre=titre_input, description=description_input, url_image=relative_path_succes)
            session.add(succes)
            session.commit()

        #create table Projets_Medias
        #if succes is not referenced
        if titre_input is None and description_input is None:
            projet_tranmedia = Projets_Transmedias(id_projets_transmedias=(session.query(func.max(Projets_Transmedias.id_projets_transmedias)).scalar() or 0) + 1, id_fiche=fiche.id_fiches, id_avis=avis.id_avis, id_notes=notes.id_notes, titre=None)
            session.add(projet_tranmedia)
            session.commit()
        else:
            projet_tranmedia = Projets_Transmedias(id_projets_transmedias=(session.query(func.max(Projets_Transmedias.id_projets_transmedias)).scalar() or 0) + 1, id_fiche=fiche.id_fiches, id_avis=avis.id_avis, id_notes=notes.id_notes, titre=succes.titre)
            session.add(projet_tranmedia)
            session.commit()

        # create table Nommer_T
        for alternative_name in alternative_names:
            if alternative_name != "":
                nommer_t = Nommer_T(id_projets_transmedias=projet_tranmedia.id_projets_transmedias,
                                    nom_alternatif=session.query(Noms_Alternatifs).filter(
                                        Noms_Alternatifs.nom_alternatif == alternative_name).first().nom_alternatif)
                session.add(nommer_t)
                session.commit()

    except:
        # En cas d'erreur, annulez la transaction
        insertion.rollback()
        print(Exception)
        make_response(jsonify({'message': 'Les données saisie semble être invalides, veuillez les vérifier. Contacter un administrateur si besoin'}), 400)
    finally:
        # Fermer la session
        session.close()

    return make_response(jsonify({'message': "Tout marche bien" }), 200)

