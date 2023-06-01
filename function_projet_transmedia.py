from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response, g
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal, case, distinct, Float
from config import *
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
	verify_jwt_in_request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import Integer, String
from cache import cache
from sqlalchemy.sql.expression import case, cast
from sqlalchemy.dialects.postgresql import array_agg, aggregate_order_by

def is_request_from_bot(user_agent):
	bot_identifiers = ['bot', 'spider', 'crawl', 'slurp', 'bingpreview', 'mediapartners-google']
	return True if any(bot_identifier in user_agent.lower() for bot_identifier in bot_identifiers) else False

@cache.memoize(timeout=24*60*60) # cache durée de 24 heures
def get_objective_data(id_projet_transmedia, session):
	# Sous-requête pour obtenir l'id_fiche correspondant à l'id_produit_culturel
	subquery_fiche = session.query(
		Projets_Transmedias.id_fiches
	).filter(
		Projets_Transmedias.id_projets_transmedias == id_projet_transmedia
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
		Projets_Transmedias.id_projets_transmedias,
		func.coalesce(func.count(Posseder_T.pseudo), 0).label("nombre_possessions")
	).join(
		Posseder_T, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias, isouter=True
	).group_by(Projets_Transmedias.id_projets_transmedias).subquery()

	subquery_total = session.query(
		Projets_Transmedias.id_projets_transmedias,
		func.coalesce(func.count(Contenir.id_projets_medias), 0).label("projets_medias_total")
	).join(
		Contenir, Projets_Transmedias.id_projets_transmedias == Contenir.id_projets_transmedias, isouter=True
	).group_by(Projets_Transmedias.id_projets_transmedias).subquery()

	subquery_commentaires = session.query(
		Projets_Transmedias.id_projets_transmedias,
		func.count(Etre_Commente_T.id_commentaires).label("nombre_commentaires")
	).select_from(Projets_Transmedias).outerjoin(
		Etre_Commente_T,
		Projets_Transmedias.id_projets_transmedias == Etre_Commente_T.id_projets_transmedias
	).group_by(Projets_Transmedias.id_projets_transmedias).subquery()

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
		Projets_Transmedias.id_projets_transmedias,
		func.rank().over(order_by=subquery_notes.c.moyenne_notes.desc()).label("rank_note")
	).join(
		subquery_notes, Projets_Transmedias.id_fiches == subquery_notes.c.id_fiches
	).subquery()

	# Sous-requête pour obtenir le top 500 des produits les plus favorisés
	subquery_rank_favoris = session.query(
		Projets_Transmedias.id_projets_transmedias,
		func.rank().over(order_by=subquery_favoris.c.nombre_favoris.desc()).label("rank_favoris")
	).join(
		subquery_favoris, Projets_Transmedias.id_fiches == subquery_favoris.c.id_fiches
	).subquery()

	# Sous-requête pour obtenir le top 500 des produits les plus possédés
	subquery_rank_possession = session.query(
		Projets_Transmedias.id_projets_transmedias,
		func.rank().over(order_by=subquery_possession.c.nombre_possessions.desc()).label("rank_possession")
	).join(
		subquery_possession, Projets_Transmedias.id_projets_transmedias == subquery_possession.c.id_projets_transmedias
	).subquery()

	# Sous-requête pour obtenir le top 500 des produits les plus consultés
	subquery_rank_consultations = session.query(
		Projets_Transmedias.id_projets_transmedias,
		func.rank().over(order_by=Fiches.consultation.desc()).label("rank_consultation")
	).join(
		Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches
	).subquery()

	# Sous-requête pour récupérer les noms alternatifs
	subquery_noms_alternatifs = session.query(
		Nommer_T.id_projets_transmedias,
		array_agg(Noms_Alternatifs.nom_alternatif).label("noms_alternatifs")
	).join(
		Noms_Alternatifs, Nommer_T.nom_alternatif == Noms_Alternatifs.nom_alternatif
	).group_by(
		Nommer_T.id_projets_transmedias
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
		Fiches.nom,
		Fiches.synopsis,
		Fiches.contributeur,
		Fiches.url_image,
		Fiches.adulte,
		Fiches.info,
		Fiches.concepteur,
		Succes.titre,
		Succes.description,
		Succes.url_image.label("url_image_succes"),
		func.coalesce(subquery_notes.c.nombre_notes, 0).label("nombre_notes"),
		func.coalesce(subquery_notes.c.moyenne_notes, 0).label("moyenne_notes"),
		func.coalesce(subquery_favoris.c.nombre_favoris, 0).label("nombre_favoris"),
		func.coalesce(subquery_possession.c.nombre_possessions, 0).label("nombre_possessions"),
		func.coalesce(subquery_total.c.projets_medias_total, 0).label("projets_medias_total"),
		func.coalesce(subquery_commentaires.c.nombre_commentaires, 0).label("nombre_commentaires"),
		func.coalesce(subquery_rank_note.c.rank_note, 0).label("rank_note"),
		func.coalesce(subquery_rank_favoris.c.rank_favoris, 0).label("rank_favoris"),
		func.coalesce(subquery_rank_possession.c.rank_possession, 0).label("rank_possession"),
		func.coalesce(subquery_rank_consultations.c.rank_consultation, 0).label("rank_consultation"),
		# Ajout des proportions de avis_popularite et avis_cote à la requête
		*[sub.c[f"proportion_popularite_{i-1}"] for i, sub in enumerate(subquery_popularite)],
		*[sub.c[f"proportion_cote_{i-1}"] for i, sub in enumerate(subquery_cote)],
		subquery_noms_alternatifs.c.noms_alternatifs,
		*[sub.c[f"proportion_note_{i}"] for i, sub in enumerate(subquery_repartition_notes)],
	).select_from(
		Projets_Transmedias,
	).join(
		Fiches,
		Projets_Transmedias.id_fiches == Fiches.id_fiches
	).outerjoin(
		Succes,
		Projets_Transmedias.titre == Succes.titre
	).outerjoin(
		subquery_notes,
		Projets_Transmedias.id_fiches == subquery_notes.c.id_fiches
	).outerjoin(
		subquery_favoris,
		Projets_Transmedias.id_fiches == subquery_favoris.c.id_fiches
	).outerjoin(
		subquery_possession,
		Projets_Transmedias.id_projets_transmedias == subquery_possession.c.id_projets_transmedias
	).outerjoin(
		subquery_total,
		Projets_Transmedias.id_projets_transmedias == subquery_total.c.id_projets_transmedias
	).outerjoin(
		subquery_commentaires,
		Projets_Transmedias.id_projets_transmedias == subquery_commentaires.c.id_projets_transmedias
	).outerjoin(
		subquery_rank_note,
		Projets_Transmedias.id_projets_transmedias == subquery_rank_note.c.id_projets_transmedias
	).outerjoin(
		subquery_rank_favoris,
		Projets_Transmedias.id_projets_transmedias == subquery_rank_favoris.c.id_projets_transmedias
	).outerjoin(
		subquery_rank_possession,
		Projets_Transmedias.id_projets_transmedias == subquery_rank_possession.c.id_projets_transmedias
	).outerjoin(
		subquery_rank_consultations,
		Projets_Transmedias.id_projets_transmedias == subquery_rank_consultations.c.id_projets_transmedias
	).outerjoin(
		subquery_noms_alternatifs,
		Projets_Transmedias.id_projets_transmedias == subquery_noms_alternatifs.c.id_projets_transmedias
	)

	# Ajout de chaque sous-requête de popularite et cote en tant qu'outerjoin distinct
	for sub in subquery_popularite:
		produit = produit.outerjoin(
			sub, Projets_Transmedias.id_fiches == sub.c.id_fiches
		)

	for sub in subquery_cote:
		produit = produit.outerjoin(
			sub, Projets_Transmedias.id_fiches == sub.c.id_fiches
		)

	for sub in subquery_repartition_notes:
		produit = produit.outerjoin(
			sub, Projets_Transmedias.id_fiches == sub.c.id_fiches
		)

	produit = produit.filter(
		Projets_Transmedias.id_projets_transmedias == id_projet_transmedia,
		Projets_Transmedias.verifie == True
	).first()

	return produit


def projet_transmedia_app(session, id_projet_transmedia, client, user_agent):
	info_user = None
	isadulte = False
	# check if projet transmedia exist
	if not session.query(Projets_Transmedias).filter(Projets_Transmedias.id_projets_transmedias == id_projet_transmedia).first():
		return jsonify({"error": "Le Projet Transmedia exigé n'est pas présent dans nos données"}), 404

	verify_jwt_in_request(optional=True)
	if current_user.is_authenticated or get_jwt_identity() is not None:
		if current_user.is_authenticated:
			user = current_user.pseudo
			isadulte = current_user.adulte
		else:
			user = get_jwt_identity()
			isadulte = session.execute(
				select(Utilisateurs.adulte).where(Utilisateurs.pseudo == get_jwt_identity())).scalar()

		sub_query_transmedia_possedes = session.query(
			Posseder_T.id_projets_transmedias,
			func.count(distinct(case((Posseder_M.pseudo == user, Posseder_M.id_projets_medias)))).label('projets_medias_possedes')
		).select_from(Posseder_T) \
		.join(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias) \
		.join(Contenir, Contenir.id_projets_transmedias == Projets_Transmedias.id_projets_transmedias) \
		.join(Projets_Medias, Projets_Medias.id_projets_medias == Contenir.id_projets_medias) \
		.join(Posseder_M, Posseder_M.id_projets_medias == Projets_Medias.id_projets_medias) \
		.filter(Posseder_T.pseudo == user) \
		.group_by(Posseder_T.id_projets_transmedias) \
		.subquery()

		sub_query_projets_medias = session.query(
			Contenir.id_projets_transmedias,
			array_agg(aggregate_order_by(Contenir.id_projets_medias, Contenir.id_projets_medias.desc())).label(
				'projets_medias_ids'),
			array_agg(
				aggregate_order_by(func.coalesce(Posseder_M.pseudo == user, False), Contenir.id_projets_medias.desc())).label(
				'projets_medias_bool_possede')
		).join(Posseder_M, Posseder_M.id_projets_medias == Contenir.id_projets_medias, isouter=True) \
			.filter(Contenir.id_projets_transmedias == id_projet_transmedia) \
			.group_by(Contenir.id_projets_transmedias).subquery()

		info_user = session.query(
			Avis.favori, Avis.avis_popularite, Avis.avis_cote, Notes.note,
			Posseder_T.date_ajout,
			sub_query_transmedia_possedes.c.projets_medias_possedes,
			sub_query_projets_medias.c.projets_medias_ids,
			sub_query_projets_medias.c.projets_medias_bool_possede
		).select_from(Projets_Transmedias) \
			.outerjoin(Avis, and_(Projets_Transmedias.id_fiches == Avis.id_fiches, Avis.pseudo == user)) \
			.outerjoin(Notes, and_(Projets_Transmedias.id_fiches == Notes.id_fiches, Notes.pseudo == user)) \
			.outerjoin(Fiches, Projets_Transmedias.id_fiches == Fiches.id_fiches) \
			.outerjoin(Contenir, Projets_Transmedias.id_projets_transmedias == Contenir.id_projets_medias) \
			.outerjoin(Posseder_T, and_(Projets_Transmedias.id_projets_transmedias == Posseder_T.id_projets_transmedias,
										Posseder_T.pseudo == user)) \
			.outerjoin(sub_query_transmedia_possedes,
					   Posseder_T.id_projets_transmedias == sub_query_transmedia_possedes.c.id_projets_transmedias) \
			.outerjoin(sub_query_projets_medias,
					   Projets_Transmedias.id_projets_transmedias == sub_query_projets_medias.c.id_projets_transmedias) \
			.filter(Projets_Transmedias.id_projets_transmedias == id_projet_transmedia).first()

	else:
		user = g.user
		isadulte = False

	transmedia = get_objective_data(id_projet_transmedia, session)


	fiche = session.query(Fiches) \
		.select_from(Projets_Transmedias).join(Fiches) \
		.filter(Projets_Transmedias.id_fiches == Fiches.id_fiches) \
		.filter(Projets_Transmedias.id_projets_transmedias == id_projet_transmedia).first()

	if not is_request_from_bot(user_agent):
		if fiche is not None:
			if fiche.consultation is None:
				fiche.consultation = 1
			else:
				fiche.consultation += 1
			session.commit()

	commentaires = session.query(Commentaires.pseudo, Commentaires.contenu, cast(Commentaires.date_post, String), Commentaires.spoiler, Commentaires.adulte) \
	.select_from(Projets_Transmedias).outerjoin(Etre_Commente_T, Projets_Transmedias.id_projets_transmedias == Etre_Commente_T.id_projets_transmedias) \
	.outerjoin(Commentaires, Etre_Commente_T.id_commentaires == Commentaires.id_commentaires) \
	.filter(Projets_Transmedias.id_projets_transmedias == id_projet_transmedia)\
	.filter(Commentaires.signale == False)\
	.order_by(Commentaires.date_post.desc()).all()

	transmedia_is_adulte = session.execute(select(Fiches.adulte).join(Fiches).select_from(Projets_Transmedias).filter(Projets_Transmedias.id_fiches == Fiches.id_fiches).filter(Projets_Transmedias.id_projets_transmedias == id_projet_transmedia))

	reponse = {
		"commentaires": [{"pseudo": pseudo, "contenu": contenu, "date_post": date_post, "spoiler": spoiler, "adulte": adulte} for pseudo, contenu, date_post, spoiler, adulte in commentaires],
		"transmedia": {column: getattr(transmedia, column) for column in transmedia._fields},
		"info_user": {column: getattr(info_user, column) for column in info_user._fields} if info_user else None,
		"consultation": fiche.consultation if fiche else None,
	}

	if isadulte or transmedia_is_adulte or session.get('adulte', False):
		if client == 'app':
			return jsonify(reponse)
		else:
			return render_template("projet_transmedia.html", activate_adulte_js_verification=False, **reponse)
	else:
		if client == 'app':
			return jsonify(reponse)
		else:
			return render_template("projet_transmedia.html", activate_adulte_js_verification=True, **reponse)


