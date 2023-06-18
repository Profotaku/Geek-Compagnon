from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response, g
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal, case, distinct, Float, \
	cast, String
from config import *
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    verify_jwt_in_request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import Integer
from cache import cache
from sqlalchemy.sql.expression import case
from sqlalchemy.dialects.postgresql import array_agg


def is_request_from_bot(user_agent):
	bot_identifiers = ['bot', 'spider', 'crawl', 'slurp', 'bingpreview', 'mediapartners-google']
	return True if any(bot_identifier in user_agent.lower() for bot_identifier in bot_identifiers) else False
@cache.memoize(timeout=24*60*60) # cache durée de 24 heures
def get_objective_data(id_produit_culturel, session):
	# Sous-requête pour obtenir l'id_fiche correspondant à l'id_produit_culturel
	subquery_fiche = session.query(
		Produits_Culturels.id_fiches
	).filter(
		Produits_Culturels.id_produits_culturels == id_produit_culturel
	).subquery()

	# Sous-requêtes pour les calculs
	subquery_notes = session.query(
		Notes.id_fiches,
		func.coalesce(func.count(Notes.note), 0).label("nombre_notes"),
		func.coalesce(func.avg(Notes.note), 0).label("moyenne_notes"),
	).join(
		subquery_fiche, Notes.id_fiches == subquery_fiche.c.id_fiches, isouter=True
	).group_by(Notes.id_fiches).subquery()

	subquery_favoris = session.query(
		Avis.id_fiches,
		func.count(Avis.favori).label("nombre_favoris")
	).join(
		subquery_fiche, Avis.id_fiches == subquery_fiche.c.id_fiches
	).filter(
		Avis.favori == True
	).group_by(Avis.id_fiches).subquery()

	subquery_possession = session.query(
		Produits_Culturels.id_produits_culturels,
		func.coalesce(func.count(Posseder_C.pseudo), 0).label("nombre_possessions")
	).join(
		Posseder_C, Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels, isouter=True
	).group_by(Produits_Culturels.id_produits_culturels).subquery()

	subquery_commentaires = session.query(
		Produits_Culturels.id_produits_culturels,
		func.count(Etre_Commente_C.id_commentaires).label("nombre_commentaires")
	).select_from(Produits_Culturels).outerjoin(
		Etre_Commente_C,
		Produits_Culturels.id_produits_culturels == Etre_Commente_C.id_produits_culturels
	).group_by(Produits_Culturels.id_produits_culturels).subquery()

	# Sous-requête pour les proportions de avis_popularite
	subquery_popularite = []
	for i in range(-1, 2):  # -1 = dislike, 0 = neutre, 1 = like
		sub = session.query(
			Avis.id_fiches,
			(func.sum(case((Avis.avis_popularite == i, 1), else_=0)) / func.coalesce(
				func.sum(case((Avis.avis_popularite != None, 1), else_=0)), 1).cast(Float)).label(
				f"proportion_popularite_{i}")
		).join(
			subquery_fiche, Avis.id_fiches == subquery_fiche.c.id_fiches
		).group_by(Avis.id_fiches).subquery()

		subquery_popularite.append(sub)

	# Sous-requête pour les proportions de avis_cote
	subquery_cote = []
	for i in range(-1, 2):  # -1 = dislike, 0 = neutre, 1 = like
		sub = session.query(
			Avis.id_fiches,
			(func.sum(case((Avis.avis_cote == i, 1), else_=0)) / func.coalesce(
				func.sum(case((Avis.avis_cote != None, 1), else_=0)), 1).cast(
				Float)).label(f"proportion_cote_{i}")
		).join(
			subquery_fiche, Avis.id_fiches == subquery_fiche.c.id_fiches
		).group_by(Avis.id_fiches).subquery()

		subquery_cote.append(sub)

	# Sous-requête pour obtenir le top 500 des produits les mieux notés
	subquery_rank_note = session.query(
		Produits_Culturels.id_produits_culturels,
		func.rank().over(order_by=subquery_notes.c.moyenne_notes.desc()).label("rank_note")
	).join(
		subquery_notes, Produits_Culturels.id_fiches == subquery_notes.c.id_fiches
	).subquery()

	# Sous-requête pour obtenir le top 500 des produits les plus favorisés
	subquery_rank_favoris = session.query(
		Produits_Culturels.id_produits_culturels,
		func.rank().over(order_by=subquery_favoris.c.nombre_favoris.desc()).label("rank_favoris")
	).join(
		subquery_favoris, Produits_Culturels.id_fiches == subquery_favoris.c.id_fiches
	).subquery()

	# Sous-requête pour obtenir le top 500 des produits les plus possédés
	subquery_rank_possession = session.query(
		Produits_Culturels.id_produits_culturels,
		func.rank().over(order_by=subquery_possession.c.nombre_possessions.desc()).label("rank_possession")
	).join(
		subquery_possession, Produits_Culturels.id_produits_culturels == subquery_possession.c.id_produits_culturels
	).subquery()

	# Sous-requête pour obtenir le top 500 des produits les plus consultés
	subquery_rank_consultations = session.query(
		Produits_Culturels.id_produits_culturels,
		func.rank().over(order_by=Fiches.consultation.desc()).label("rank_consultation")
	).join(
		Fiches, Produits_Culturels.id_fiches == Fiches.id_fiches
	).subquery()

	# Sous-requête pour récupérer les genres
	subquery_genres = session.query(
		Etre_Defini.id_produits_culturels,
		array_agg(Genres.nom_genres).label("genres")
	).join(
		Genres, Etre_Defini.nom_genres == Genres.nom_genres
	).group_by(
		Etre_Defini.id_produits_culturels
	).subquery()

	# Sous-requête pour récupérer les EAN13
	subquery_ean13 = session.query(
		Etre_Identifie.id_produits_culturels,
		array_agg(EAN13.ean13).label("ean13")
	).join(
		EAN13, Etre_Identifie.ean13 == EAN13.ean13
	).group_by(
		Etre_Identifie.id_produits_culturels
	).subquery()

	# Sous-requête pour récupérer les noms alternatifs
	subquery_noms_alternatifs = session.query(
		Nommer_C.id_produits_culturels,
		array_agg(Noms_Alternatifs.nom_alternatif).label("noms_alternatifs")
	).join(
		Noms_Alternatifs, Nommer_C.nom_alternatif == Noms_Alternatifs.nom_alternatif
	).group_by(
		Nommer_C.id_produits_culturels
	).subquery()

	# Sous-requêtes pour la répartition des notes
	subquery_repartition_notes = []
	for i in range(11):  # 0 à 10
		sub = session.query(
			Notes.id_fiches,
			(func.sum(case((Notes.note == i, 1), else_=0)) / func.coalesce(
				func.sum(case((Notes.note != None, 1), else_=0)), 1).cast(Float)).label(
				f"proportion_note_{i}")
		).join(
			subquery_fiche, Notes.id_fiches == subquery_fiche.c.id_fiches
		).group_by(Notes.id_fiches).subquery()

		subquery_repartition_notes.append(sub)

	# Requête principale
	produit = session.query(
		Produits_Culturels.date_sortie,
		Produits_Culturels.nom_types_media,
		Fiches.nom,
		Fiches.synopsis,
		Fiches.contributeur,
		Fiches.url_image,
		Fiches.adulte,
		Fiches.info,
		Fiches.concepteur,
		func.coalesce(subquery_notes.c.nombre_notes, 0).label("nombre_notes"),
		func.coalesce(subquery_notes.c.moyenne_notes, 0).label("moyenne_notes"),
		func.coalesce(subquery_favoris.c.nombre_favoris, 0).label("nombre_favoris"),
		func.coalesce(subquery_possession.c.nombre_possessions, 0).label("nombre_possessions"),
		func.coalesce(subquery_commentaires.c.nombre_commentaires, 0).label("nombre_commentaires"),
		func.coalesce(subquery_rank_note.c.rank_note, 0).label("rank_note"),
		func.coalesce(subquery_rank_favoris.c.rank_favoris, 0).label("rank_favoris"),
		func.coalesce(subquery_rank_possession.c.rank_possession, 0).label("rank_possession"),
		func.coalesce(subquery_rank_consultations.c.rank_consultation, 0).label("rank_consultation"),
		subquery_genres.c.genres,
		subquery_ean13.c.ean13,
		subquery_noms_alternatifs.c.noms_alternatifs,
		# Ajout des proportions de avis_popularite et avis_cote à la requête
		*[func.coalesce(sub.c[f"proportion_popularite_{i-1}"], 0).label(f"proportion_popularite_{i-1}") for i, sub in enumerate(subquery_popularite)],
		*[func.coalesce(sub.c[f"proportion_cote_{i-1}"], 0).label(f"proportion_cote_{i-1}") for i, sub in enumerate(subquery_cote)],
		*[func.coalesce(sub.c[f"proportion_note_{i}"], 0).label(f"proportion_note_{i}") for i, sub in enumerate(subquery_repartition_notes)],
	).join(
		Fiches,
		Produits_Culturels.id_fiches == Fiches.id_fiches
	).outerjoin(
		subquery_notes,
		Produits_Culturels.id_fiches == subquery_notes.c.id_fiches
	).outerjoin(
		subquery_favoris,
		Produits_Culturels.id_fiches == subquery_favoris.c.id_fiches
	).outerjoin(
		subquery_possession,
		Produits_Culturels.id_produits_culturels == subquery_possession.c.id_produits_culturels
	).outerjoin(
		subquery_commentaires,
		Produits_Culturels.id_produits_culturels == subquery_commentaires.c.id_produits_culturels
	).outerjoin(
		subquery_rank_note,
		Produits_Culturels.id_produits_culturels == subquery_rank_note.c.id_produits_culturels
	).outerjoin(
		subquery_rank_favoris,
		Produits_Culturels.id_produits_culturels == subquery_rank_favoris.c.id_produits_culturels
	).outerjoin(
		subquery_rank_possession,
		Produits_Culturels.id_produits_culturels == subquery_rank_possession.c.id_produits_culturels
	).outerjoin(
		subquery_rank_consultations,
		Produits_Culturels.id_produits_culturels == subquery_rank_consultations.c.id_produits_culturels
	).outerjoin(
		subquery_genres,
		Produits_Culturels.id_produits_culturels == subquery_genres.c.id_produits_culturels
	).outerjoin(
		subquery_ean13,
		Produits_Culturels.id_produits_culturels == subquery_ean13.c.id_produits_culturels
	).outerjoin(
		subquery_noms_alternatifs,
		Produits_Culturels.id_produits_culturels == subquery_noms_alternatifs.c.id_produits_culturels
	)

	# Ajout de chaque sous-requête de popularite et cote en tant qu'outerjoin distinct
	for sub in subquery_popularite:
		produit = produit.outerjoin(
			sub, Produits_Culturels.id_fiches == sub.c.id_fiches
		)

	for sub in subquery_cote:
		produit = produit.outerjoin(
			sub, Produits_Culturels.id_fiches == sub.c.id_fiches
		)

	for sub in subquery_repartition_notes:
		produit = produit.outerjoin(
			sub, Produits_Culturels.id_fiches == sub.c.id_fiches
		)

	produit = produit.filter(
		Produits_Culturels.id_produits_culturels == id_produit_culturel,
		Produits_Culturels.verifie == True
	).first()

	return produit


def produit_culturel_app(session, id_produit_culturel, client, user_agent):
	info_user = None
	isadulte = False
	# check if produit culturel is in database
	if not session.query(Produits_Culturels).filter_by(id_produits_culturels=id_produit_culturel, verifie=True).first():
		return jsonify({"error": "La fiche produit exigée n'est pas présente dans nos données"}), 404

	verify_jwt_in_request(optional=True)
	if current_user.is_authenticated or get_jwt_identity() is not None:
		if current_user.is_authenticated:
			user = current_user.pseudo
			isadulte = current_user.adulte
		else:
			user = get_jwt_identity()
			isadulte = session.execute(
				select(Utilisateurs.adulte).where(Utilisateurs.pseudo == get_jwt_identity())).scalar()

		info_user = session.query(
			Avis.favori, Avis.avis_popularite, Avis.avis_cote, Notes.note,
			Posseder_C.physiquement, Posseder_C.souhaite, Posseder_C.date_ajout,
			Posseder_C.limite, Posseder_C.collector
		).select_from(Produits_Culturels) \
			.outerjoin(Avis, and_(Produits_Culturels.id_fiches == Avis.id_fiches, Avis.pseudo == user)) \
			.outerjoin(Notes, and_(Produits_Culturels.id_fiches == Notes.id_fiches, Notes.pseudo == user)) \
			.outerjoin(Fiches, Produits_Culturels.id_fiches == Fiches.id_fiches) \
			.outerjoin(Posseder_C, and_(Produits_Culturels.id_produits_culturels == Posseder_C.id_produits_culturels,
										Posseder_C.pseudo == user)) \
			.filter(Produits_Culturels.id_produits_culturels == id_produit_culturel).first()
	else:
		user = g.user
		isadulte = False

	# Get static data from cache
	produit = get_objective_data(id_produit_culturel, session)

	fiche = session.query(Fiches) \
		.select_from(Produits_Culturels).join(Fiches) \
		.filter(Produits_Culturels.id_fiches == Fiches.id_fiches) \
		.filter(Produits_Culturels.id_produits_culturels == id_produit_culturel).first()
	if not is_request_from_bot(user_agent):
		if fiche is not None:
			if fiche.consultation is None:
				fiche.consultation = 1
			else:
				fiche.consultation += 1
			session.commit()

	commentaires = session.query(Commentaires.pseudo, Commentaires.contenu, cast(Commentaires.date_post, String), Commentaires.spoiler, Commentaires.adulte) \
	.select_from(Produits_Culturels).outerjoin(Etre_Commente_C, Produits_Culturels.id_produits_culturels == Etre_Commente_C.id_produits_culturels) \
	.outerjoin(Commentaires, Etre_Commente_C.id_commentaires == Commentaires.id_commentaires) \
	.filter(Produits_Culturels.id_produits_culturels == id_produit_culturel)\
	.filter(Commentaires.signale == False)\
	.order_by(Commentaires.date_post.desc()).all()

	produit_is_adulte = session.execute(select(Fiches.adulte).join(Fiches).select_from(Produits_Culturels).filter(Produits_Culturels.id_fiches == Fiches.id_fiches).filter(Produits_Culturels.id_produits_culturels == id_produit_culturel))

	reponse = {
		"commentaires": [{"pseudo": pseudo, "contenu": contenu, "date_post": date_post, "spoiler": spoiler, "adulte": adulte} for pseudo, contenu, date_post, spoiler, adulte in commentaires],
		"produit": {column: getattr(produit, column) for column in produit._fields} if produit else None,
		"info_user": {column: getattr(info_user, column) for column in info_user._fields} if info_user else None,
		"consultation": fiche.consultation if fiche else None
	}

	if isadulte or produit_is_adulte or session.get('adulte', False):
		if client == 'app':
			return jsonify(reponse)
		else:
			return render_template("public/produit_culturel.html", activate_adulte_js_verification=False, **reponse)
	else:
		if client == 'app':
			return jsonify(reponse)
		else:
			return render_template("public/produit_culturel.html", activate_adulte_js_verification=True, **reponse)


