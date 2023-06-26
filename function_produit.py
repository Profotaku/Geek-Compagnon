from sqlalchemy import func, and_

from dataclass import *
from sqlalchemy.orm import joinedload, aliased
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_file, make_response, g
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_login import login_user, logout_user, current_user, login_required

def calculer_taux_completion_media(collection, pseudo, session):
	total_produits = session.query(Produits_Culturels). \
		join(Etre_Compose). \
		join(Projets_Medias). \
		filter_by(id_projets_medias=collection.id_projets_medias). \
		count()
	produits_possedes = session.query(Produits_Culturels). \
		join(Etre_Compose). \
		join(Projets_Medias). \
		filter_by(id_projets_medias=collection.id_projets_medias). \
		join(Posseder_C). \
		filter_by(pseudo=pseudo). \
		count()
	return (produits_possedes,total_produits) if total_produits else (0,0)

def calculer_taux_completion_transmedia(collection, pseudo, session):
	total_collection = session.query(Projets_Medias). \
		join(Contenir). \
		join(Projets_Transmedias). \
		filter_by(id_projets_transmedias=collection.id_projets_transmedias). \
		count()
	collections_possedes = session.query(Projets_Medias). \
		join(Contenir). \
		join(Projets_Transmedias). \
		filter_by(id_projets_transmedias=collection.id_projets_transmedias). \
		join(Posseder_M). \
		filter_by(pseudo=pseudo). \
		count()
	return (collections_possedes,total_collection) if total_collection else (0,0)
def ajouter_produit(session, client):
	verify_jwt_in_request(optional=True)
	if client == "app":
		user = get_jwt_identity()
		user = session.query(Utilisateurs).filter(Utilisateurs.pseudo == user).first()
	else:
		user = session.query(Utilisateurs).filter(Utilisateurs.pseudo == current_user.pseudo).first()
	# Récupérer les informations du formulaire
	id_produit = request.form.get('id_produit')
	physiquement = bool(request.form.get('physiquement')) if request.form.get('physiquement') else False
	souhaite = bool(request.form.get('souhaite')) if request.form.get('souhaite') else False
	limite = bool(request.form.get('limite')) if request.form.get('limite') else False
	collector = bool(request.form.get('collector')) if request.form.get('collector') else False
	note = int(request.form.get('note'))
	favori = bool(request.form.get('favori')) if request.form.get('favori') else False
	avis_popularite = int(request.form.get('avis_popularite'))
	avis_cote = int(request.form.get('avis_cote'))

	try :
		# Vérifier si le produit est déjà dans la collection de l'utilisateur
		possession = session.query(Posseder_C).filter(and_(Posseder_C.id_produits_culturels == id_produit, Posseder_C.pseudo == user.pseudo)).first()
		produit = session.query(Produits_Culturels).filter(Produits_Culturels.id_produits_culturels == id_produit).first()
		note_user = session.query(Notes).filter(and_(Notes.id_fiches == produit.id_fiches, Notes.pseudo == user.pseudo)).first()
		avis_user = session.query(Avis).filter(and_(Avis.id_fiches == produit.id_fiches, Avis.pseudo == user.pseudo)).first()

		if possession is not None:
			# Si le produit est déjà dans la collection, mettre à jour les valeurs
			possession.physiquement = physiquement
			possession.souhaite = souhaite
			possession.limite = limite
			possession.collector = collector
		else:
			# Sinon, créer une nouvelle entrée dans la table
			possession = Posseder_C(
				id_produits_culturels=id_produit,
				pseudo=user.pseudo,
				physiquement=physiquement,
				souhaite=souhaite,
				limite=limite,
				collector=collector,
			)
			session.add(possession)
			user.experience += 10  # Augmenter l'expérience de l'utilisateur
			# Obtenir tous les projets medias liés au produit culturel
			etre_compose = session.query(Etre_Compose).filter(Etre_Compose.id_produits_culturels == id_produit).all()
			for ec in etre_compose:
				projet_media = session.query(Projets_Medias).filter(
					Projets_Medias.id_projets_medias == ec.id_projets_medias).first()

				# Vérifier si l'utilisateur possède déjà le projet media
				possession_m = session.query(Posseder_M).filter(
					and_(Posseder_M.id_projets_medias == projet_media.id_projets_medias,
					     Posseder_M.pseudo == user.pseudo)).first()

				if possession_m is None:
					# Si l'utilisateur ne possède pas le projet media, l'ajouter à la table Posseder_M
					new_possession_m = Posseder_M(
						id_projets_medias=projet_media.id_projets_medias,
						pseudo=user.pseudo,
					)
					session.add(new_possession_m)
					user.experience += 5

					# Rechercher les projets transmedias liés au projet media
					contenir = session.query(Contenir).filter(
						Contenir.id_projets_medias == projet_media.id_projets_medias).all()
					for c in contenir:
						projet_transmedia = session.query(Projets_Transmedias).filter(
							Projets_Transmedias.id_projets_transmedias == c.id_projets_transmedias).first()

						# Vérifier si l'utilisateur possède déjà le projet transmedia
						possession_t = session.query(Posseder_T).filter(
							and_(Posseder_T.id_projets_transmedias == projet_transmedia.id_projets_transmedias, Posseder_T.pseudo == user.pseudo)).first()

						if possession_t is None:
							# Si l'utilisateur ne possède pas le projet transmedia, l'ajouter à la table Posseder_T
							new_possession_t = Posseder_T(
								id_projets_transmedias=projet_transmedia.id_projets_transmedias,
								pseudo=user.pseudo,
							)
							session.add(new_possession_t)

							# Ajouter 5 points d'expérience pour l'ajout d'un premier projet media à un projet transmedia
							user.experience += 2

					# Calculer le taux de complétion de la collection
					produits_possedes, total_produits = calculer_taux_completion_media(projet_media, user.pseudo, session)
					if produits_possedes == total_produits:
						# Si la collection est complétée, ajouter 5 * x points d'expérience
						user.experience += 5 * total_produits

						# Calculer le taux de complétion du projet transmedia
						collections_possedes, total_collection = calculer_taux_completion_transmedia(projet_transmedia, user.pseudo, session)
						if collections_possedes == total_collection:
							# Si le projet transmedia est complété, ajouter 5 * x points d'expérience
							user.experience += 2 * total_collection

		if note_user is not None:
			# Si l'utilisateur a déjà noté le produit, mettre à jour la note
			note_user.note = note
		else:
			# Sinon, créer une nouvelle note
			new_note = Notes(
				id_fiches=produit.id_fiches,
				pseudo=user.pseudo,
				note=note,
			)
			session.add(new_note)

		if avis_user is not None:
			# Si l'utilisateur a déjà donné un avis, mettre à jour l'avis
			avis_user.favori = favori
			avis_user.avis_popularite = avis_popularite
			avis_user.avis_cote = avis_cote
		else:
			# Sinon, créer un nouvel avis
			new_avis = Avis(
				id_fiches=produit.id_fiches,
				pseudo=user.pseudo,
				favori=favori,
				avis_popularite=avis_popularite,
				avis_cote=avis_cote,
			)
			session.add(new_avis)

		# Valider les modifications
		session.commit()
		flash("Produit ajouté à la collection", "success")
	except Exception as e:
		session.rollback()
		print(e)
		if client == "app":
			return jsonify({"error": "Erreur lors de l'ajout du produit à la collection"})
		else:
			flash("Erreur lors de l'ajout du produit à la collection", "error")


	if client == "app":
		return jsonify({"success": "Produit ajouté à la collection"})
	return redirect(f"{url_for('produit_culturel', id_produit_culturel=int(id_produit), client=client)}")