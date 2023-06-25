from sqlalchemy import func

from dataclass import *
from sqlalchemy.orm import joinedload, aliased
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_file, make_response, g
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_login import login_user, logout_user, current_user, login_required
FichesProduits = aliased(Fiches)
FichesProjetMedias = aliased(Fiches)
FichesProjetTransmedias = aliased(Fiches)

NotesProduits = aliased(Notes)
NotesProjetMedias = aliased(Notes)
NotesProjetTransmedias = aliased(Notes)

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

def verifier_collection_complete(id_projet_transmedia, pseudo, session):
	collections_possedes, total_collection = calculer_taux_completion_transmedia(id_projet_transmedia, pseudo, session)
	if collections_possedes != total_collection:
		return False

	sous_collections = (
		session.query(Posseder_T)
		.filter(Posseder_T.id_projets_transmedias == id_projet_transmedia)
		.all()
	)

	for sous_collection in sous_collections:
		if not verifier_collection_complete(sous_collection.id_projets_transmedias, pseudo, session):
			return False

	return True


def obtenir_succes_utilisateur_global(pseudo, session):
	image_succes_rank = ""
	image_succes_produits = ""
	image_succes_level = ""
	global_success = []
	# Obtenir l'utilisateur actuel
	user = session.query(Utilisateurs).filter(Utilisateurs.pseudo == pseudo).first()

	# Calculer le nombre total d'utilisateurs vérifiés
	total_verified_users = session.query(Utilisateurs).filter(Utilisateurs.verifie == True).count()

	# Calculer le rang de l'utilisateur courant parmi les utilisateurs vérifiés
	rank_utilisateur_courant = session.query(Utilisateurs).filter(Utilisateurs.verifie == True, Utilisateurs.date_creation <= user.date_creation).count()

	# Calculer le pourcentage d'ordre d'arrivée de l'utilisateur courant
	pourcentage = int((rank_utilisateur_courant / total_verified_users) * 100)

	# Définir le succès en fonction du pourcentage
	if pourcentage <= 1:
		image_succes_rank = "/static/images/globalsuccess/rank/1.png"
	elif pourcentage <= 5:
		image_succes_rank = "/static/images/globalsuccess/rank/5.png"
	elif pourcentage <= 10:
		image_succes_rank = "/static/images/globalsuccess/rank/10.png"
	elif pourcentage <= 25:
		image_succes_rank = "/static/images/globalsuccess/rank/25.png"
	elif pourcentage <= 50:
		image_succes_rank = "/static/images/globalsuccess/rank/50.png"

	# Compter le nombre total de produits culturels possédés par l'utilisateur
	total_produits_possedes = session.query(Posseder_C).filter(Posseder_C.pseudo == pseudo).count()

	# Définir le succès en fonction du nombre total de produits possédés
	if total_produits_possedes >= 1:
		image_succes_produits = "/static/images/globalsuccess/product_number/1.png"
	elif total_produits_possedes >= 5:
		image_succes_produits = "/static/images/globalsuccess/product_number/5.png"
	elif total_produits_possedes >= 10:
		image_succes_produits = "/static/images/globalsuccess/product_number/10.png"
	elif total_produits_possedes >= 25:
		image_succes_produits = "/static/images/globalsuccess/product_number/25.png"
	elif total_produits_possedes >= 50:
		image_succes_produits = "/static/images/globalsuccess/product_number/50.png"
	elif total_produits_possedes >= 100:
		image_succes_produits = "/static/images/globalsuccess/product_number/100.png"
	elif total_produits_possedes >= 250:
		image_succes_produits = "/static/images/globalsuccess/product_number/250.png"
	elif total_produits_possedes >= 500:
		image_succes_produits = "/static/images/globalsuccess/product_number/500.png"
	elif total_produits_possedes >= 1000:
		image_succes_produits = "/static/images/globalsuccess/product_number/1000.png"

	# Obtenir le nombre de points d'expérience de l'utilisateur
	experience_utilisateur = session.query(Utilisateurs.experience).filter(Utilisateurs.pseudo == pseudo).first()[0]
	# Calculer le niveau en utilisant une formule linéaire
	# Supposons que chaque niveau nécessite 10 points de plus que le précédent pour l'atteindre
	# Le niveau est la racine carrée de l'expérience divisée par 10
	niveau = int(int(int(experience_utilisateur) // 10) ** 0.5)

	# Définir le succès en fonction du niveau
	if niveau >= 1:
		image_succes_level = "/static/images/globalsuccess/level/1.png"
	elif niveau >= 5:
		image_succes_level = "/static/images/globalsuccess/level/5.png"
	elif niveau >= 10:
		image_succes_level = "/static/images/globalsuccess/level/10.png"
	elif niveau >= 25:
		image_succes_level = "/static/images/globalsuccess/level/25.png"
	elif niveau >= 50:
		image_succes_level = "/static/images/globalsuccess/level/50.png"
	elif niveau >= 100:
		image_succes_level = "/static/images/globalsuccess/level/100.png"

	if image_succes_produits != "":
		# Ajouter le succès à la liste des succès obtenus
		global_success.append({
			"nom_succes": f"{total_produits_possedes} produits possédés",
			"image_succes": image_succes_produits,
			"type_succes": "nombre_produits"
		})

	if image_succes_rank != "":
		global_success.append({
			"nom_succes": f"Top {pourcentage}%",
			"image_succes": image_succes_rank,
			"type_succes": "ordre_arrivee"
		})

	if image_succes_level != "":
		global_success.append({
			"nom_succes": f"Niveau {niveau}",
			"image_succes": image_succes_level,
			"type_succes": "niveau"
		})


	# Si l'utilisateur a un succès, on l'ajoute à la liste des succès
	# Ajouter le succès à la liste des succès obtenus
	if len(global_success) == 0:
		return None
	return global_success




def obtenir_succes_utilisateur(pseudo, session):
	# Compter le nombre total d'éléments dans chaque collection media
	subquery_total_elements_M = session.query(
		Etre_Compose.id_projets_medias,
		func.count(Etre_Compose.id_produits_culturels).label('total_elements')
	).group_by(Etre_Compose.id_projets_medias).subquery()

	# Compter combien d'éléments l'utilisateur possède dans chaque collection media
	subquery_elements_possedes_M = session.query(
		Posseder_C.pseudo,
		Etre_Compose.id_projets_medias,
		func.count(Etre_Compose.id_produits_culturels).label('elements_possedes')
	).join(
		Posseder_C,
		Etre_Compose.id_produits_culturels == Posseder_C.id_produits_culturels
	).filter(
		Posseder_C.pseudo == pseudo
	).group_by(
		Posseder_C.pseudo,
		Etre_Compose.id_projets_medias
	).subquery()

	# Compter le nombre de collections media complètes par l'utilisateur
	subquery_collections_completes_M = session.query(
		subquery_total_elements_M.c.id_projets_medias,
		subquery_elements_possedes_M.c.pseudo,
		func.count().label('nombre_collections_completes_M')
	).select_from(
		subquery_total_elements_M
	).outerjoin(
		subquery_elements_possedes_M,
		subquery_total_elements_M.c.id_projets_medias == subquery_elements_possedes_M.c.id_projets_medias
	).group_by(
		subquery_elements_possedes_M.c.pseudo,
		subquery_elements_possedes_M.c.elements_possedes,
		subquery_total_elements_M.c.total_elements,
		subquery_total_elements_M.c.id_projets_medias
	).having(
		func.coalesce(subquery_elements_possedes_M.c.elements_possedes, 0) == subquery_total_elements_M.c.total_elements
	).subquery()

	# Récupérer les collections médias complétées par l'utilisateur
	succes_medias = session.query(
		Succes.titre.label('nom_succes'),
		Succes.url_image.label('image_succes')
	).join(
		Projets_Medias,
		Projets_Medias.titre == Succes.titre
	).join(
		subquery_collections_completes_M,
		Projets_Medias.id_projets_medias == subquery_collections_completes_M.c.id_projets_medias
	).filter(
		subquery_collections_completes_M.c.pseudo == pseudo
	).all()

	# Compter le nombre total d'éléments dans chaque collection transmedia
	subquery_total_elements_T = session.query(
		Contenir.id_projets_transmedias,
		func.count(Contenir.id_projets_medias).label('total_elements')
	).group_by(Contenir.id_projets_transmedias).subquery()

	# Compter combien d'éléments l'utilisateur possède dans chaque collection transmedia
	subquery_elements_possedes_T = session.query(
		Posseder_M.pseudo,
		Contenir.id_projets_transmedias,
		func.count(Contenir.id_projets_medias).label('elements_possedes')
	).join(
		Posseder_M,
		Contenir.id_projets_medias == Posseder_M.id_projets_medias
	).filter(
		Posseder_M.pseudo == pseudo
	).group_by(
		Posseder_M.pseudo,
		Contenir.id_projets_transmedias
	).subquery()

	# Compter le nombre de collections transmedia complètes par l'utilisateur
	subquery_collections_completes_T = session.query(
		subquery_total_elements_T.c.id_projets_transmedias,
		subquery_elements_possedes_T.c.pseudo,
		func.count().label('nombre_collections_completes_T')
	).select_from(
		subquery_total_elements_T
	).outerjoin(
		subquery_elements_possedes_T,
		subquery_total_elements_T.c.id_projets_transmedias == subquery_elements_possedes_T.c.id_projets_transmedias
	).group_by(
		subquery_elements_possedes_T.c.pseudo,
		subquery_elements_possedes_T.c.elements_possedes,
		subquery_total_elements_T.c.total_elements,
		subquery_total_elements_T.c.id_projets_transmedias
	).having(
		func.coalesce(subquery_elements_possedes_T.c.elements_possedes, 0) == subquery_total_elements_T.c.total_elements
	).subquery()

	# Récupérer les collections transmédias complétées par l'utilisateur
	succes_transmedias = session.query(
		Succes.titre.label('nom_succes'),
		Succes.url_image.label('image_succes')
	).join(
		Projets_Transmedias,
		Projets_Transmedias.titre == Succes.titre
	).join(
		subquery_collections_completes_T,
		Projets_Transmedias.id_projets_transmedias == subquery_collections_completes_T.c.id_projets_transmedias
	).filter(
		subquery_collections_completes_T.c.pseudo == pseudo
	).all()

	global_sucess = obtenir_succes_utilisateur_global(pseudo, session)


	succes_obtenus = []
	for succes in succes_medias:
		succes_obtenus.append({
			"nom_succes": succes.nom_succes,
			"image_succes": succes.image_succes,
			"type_succes": "media"
		})

	# Convertir les succès obtenus en listes de dictionnaires
	for succes in succes_transmedias:
		succes_obtenus.append({
			"nom_succes": succes.nom_succes,
			"image_succes": succes.image_succes,
			"type_succes": "transmedia"
		})

	if global_sucess is not None:
		for succes in global_sucess:
			succes_obtenus.append({
				"nom_succes": succes["nom_succes"],
				"image_succes": succes["image_succes"],
				"type_succes": succes["type_succes"]
			})

	return succes_obtenus
def user(requested_user, numstart, client, session):
	#check si le profil de l'utilisateur existe et si il est public
	verify_jwt_in_request(optional=True)
	user = session.query(Utilisateurs).filter_by(pseudo=requested_user).first()
	if user:
		if user.profil_public or current_user.pseudo == requested_user or get_jwt_identity() == requested_user or current_user.admin:
			# Récupérez tous les projets transmedia pour l'utilisateur avec leurs collections associées
			produits_culturels = (
				session.query(Posseder_C)
				.join(Produits_Culturels, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels)
				.join(FichesProduits, Produits_Culturels.id_fiches == FichesProduits.id_fiches)
				.outerjoin(NotesProduits, FichesProduits.id_fiches == NotesProduits.id_fiches)
				.join(Etre_Compose, Produits_Culturels.id_produits_culturels == Etre_Compose.id_produits_culturels)
				.join(Projets_Medias, Etre_Compose.id_projets_medias == Projets_Medias.id_projets_medias)
				.join(FichesProjetMedias, Projets_Medias.id_fiches == FichesProjetMedias.id_fiches)
				.outerjoin(NotesProjetMedias, FichesProjetMedias.id_fiches == NotesProjetMedias.id_fiches)
				.join(Contenir, Projets_Medias.id_projets_medias == Contenir.id_projets_medias)
				.join(Projets_Transmedias, Contenir.id_projets_transmedias == Projets_Transmedias.id_projets_transmedias)
				.join(FichesProjetTransmedias, Projets_Transmedias.id_fiches == FichesProjetTransmedias.id_fiches)
				.outerjoin(NotesProjetTransmedias, FichesProjetTransmedias.id_fiches == NotesProjetTransmedias.id_fiches)
				.filter(Posseder_C.pseudo == user.pseudo)
				.options(joinedload(Posseder_C.produits_culturels, innerjoin=True)
				.subqueryload(Produits_Culturels.etre_compose)
				.joinedload(Etre_Compose.projets_medias)
				.subqueryload(Projets_Medias.contenir)
				.joinedload(Contenir.projets_transmedias))
				.order_by(Posseder_C.date_ajout.desc())
				.limit(10).offset(numstart)
				.all()
			)

			nombre_projets_transmedia = session.query(Contenir).filter(
				Contenir.id_projets_medias == Etre_Compose.id_projets_medias).count()  # for keep cache, request is splited

			# Récupérez les favoris de l'utilisateur

			favoris_produits = (
				session.query(Produits_Culturels)
				.join(Fiches, Produits_Culturels.id_fiches == Fiches.id_fiches)
				.join(Avis, Fiches.id_fiches == Avis.id_fiches)
				.filter(Avis.pseudo == user.pseudo, Avis.favori == True)
				.all()
			)

			favoris_projets_medias = (
				session.query(Projets_Medias)
				.join(Fiches, Projets_Medias.id_fiches == Fiches.id_fiches)
				.join(Avis, Fiches.id_fiches == Avis.id_fiches)
				.filter(Avis.pseudo == user.pseudo, Avis.favori == True)
				.all()
			)

			favoris_projets_transmedias = (
				session.query(Projets_Transmedias)
				.join(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches)
				.join(Avis, Fiches.id_fiches == Avis.id_fiches)
				.filter(Avis.pseudo == user.pseudo, Avis.favori == True)
				.all()
			)

			favoris_produits_data = [
				{
					'nom_produit': produit.fiche.nom,
					'url_image': produit.fiche.url_image,
					'favori': next((avis.favori for avis in produit.fiche.avis if avis.pseudo == user.pseudo), False),
				} for produit in favoris_produits
			]

			favoris_projets_medias_data = [
				{
					'nom_projet_media': projet_media.fiche.nom,
					'url_image': projet_media.fiche.url_image,
					'favori': next((avis.favori for avis in projet_media.fiche.avis if avis.pseudo == user.pseudo), False),
				} for projet_media in favoris_projets_medias
			]

			favoris_projets_transmedias_data = [
				{
					'nom_projet_transmedia': projet_transmedia.fiche.nom,
					'url_image': projet_transmedia.fiche.url_image,
					'favori': next((avis.favori for avis in projet_transmedia.fiche.avis if avis.pseudo == user.pseudo), False),
				} for projet_transmedia in favoris_projets_transmedias
			]

			data = []
			for row in produits_culturels:
				product_data = {
					'nom_produit': row.produits_culturels.fiche.nom,
					'url_image': row.produits_culturels.fiche.url_image,
					'note': next((note.note for note in row.produits_culturels.fiche.notes if note.pseudo == user.pseudo), ''),
					'favori': next((avis.favori for avis in row.produits_culturels.fiche.avis if avis.pseudo == user.pseudo), False),
					'projet_media': []
				}

				for etre_compose in row.produits_culturels.etre_compose[:10]:
					produits_possedes, total_produits = calculer_taux_completion_media(etre_compose.projets_medias, user.pseudo, session)
					collection_data = {
						'nom_projet_media': etre_compose.projets_medias.fiche.nom,
						'url_image': etre_compose.projets_medias.fiche.url_image,
						'note': next((note.note for note in etre_compose.projets_medias.fiche.notes if note.pseudo == user.pseudo), ''),
						'favori': next((avis.favori for avis in etre_compose.projets_medias.fiche.avis if avis.pseudo == user.pseudo), False),
						'taux_completion': str(produits_possedes) + "/" + str(total_produits),
						'truncated': len(etre_compose.projets_medias.contenir) > 10,
						'projet_transmedia': []
					}

					for contenir in etre_compose.projets_medias.contenir[:10]:
						collections_possedes, total_collection = calculer_taux_completion_transmedia(contenir.projets_transmedias, user.pseudo, session)
						collection_imbriquee_data = {
							'nom_projet_transmedia': contenir.projets_transmedias.fiche.nom,
							'url_image': contenir.projets_transmedias.fiche.url_image,
							'note': next(
								(note.note for note in contenir.projets_transmedias.fiche.notes if note.pseudo == user.pseudo), ''),
							'favori': next(
								(avis.favori for avis in contenir.projets_transmedias.fiche.avis if avis.pseudo == user.pseudo),
								False),
							'taux_completion': str(collections_possedes) + "/" + str(total_collection),
							'truncated': nombre_projets_transmedia > 10
						}
						collection_data['projet_transmedia'].append(collection_imbriquee_data)

					product_data['projet_media'].append(collection_data)

				data.append(product_data)

			succes_obtenus = obtenir_succes_utilisateur(user.pseudo, session)

			user_info = {
				'pseudo': user.pseudo,
				'biographie': user.biographie,
				'experience': user.experience,
				'niveau': int(int(int(user.experience) // 10) ** 0.5),
				'admin': user.admin,
				'fondateur': user.fondateur,
				'url_image': user.url_image
			}
			if client == "app":
				# Ajouter les favoris à votre structure de données existante
				data = {
					'user_info': user_info,
					'produits_culturels': data,  # Vos données existantes
					'favoris_produits': favoris_produits_data,
					'favoris_projets_medias': favoris_projets_medias_data,
					'favoris_projets_transmedias': favoris_projets_transmedias_data,
					'succes_obtenus': succes_obtenus
				}
				return make_response(jsonify(data), 200)
			else:
				if numstart == 0:
					return render_template('public/user.html', data=data, user=user.pseudo, numstart=numstart, favoris_produits=favoris_produits, favoris_projets_medias=favoris_projets_medias, favoris_projets_transmedias=favoris_projets_transmedias, succes_obtenus=succes_obtenus, user_info=user_info)
				else:
					return render_template('public/infine-scroll-user.html', data=data, numstart=numstart)
		else:
			return render_template('public/404.html'), 404
	else:
		return render_template('public/404.html'), 404
