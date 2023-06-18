from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response, g
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal, case, distinct, Float
from config import *
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
	verify_jwt_in_request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import Integer, String
from cache import cache
from sqlalchemy.sql.expression import case, cast, extract
from sqlalchemy.dialects.postgresql import array_agg, aggregate_order_by


def get_user_data(user, session, idtype="all"):

	# Check if type_media is valid
	if idtype != "all" and session.query(Types_Media).filter_by(nom_types_media=idtype).first() is None:
		return None

	if idtype == "all":
		idtype = session.execute(select(Types_Media.nom_types_media).select_from(Types_Media).distinct()).all()
		idtype = [row[0] for row in idtype]
	else:
		idtype = [idtype]

	subquery_possession = session.query(
		func.coalesce(func.count(Posseder_C.id_produits_culturels), 0).label("nombre_possessions")
	).join(Produits_Culturels, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels)\
	.filter(
		Posseder_C.pseudo == user,
		Produits_Culturels.nom_types_media.in_(idtype)
	).subquery()

	# Sous-requête pour obtenir les achats par année
	subquery_produits_par_annee = session.query(
		Posseder_C.pseudo,
		extract('year', Posseder_C.date_ajout).label('annee'),
		func.count(Posseder_C.id_produits_culturels).label('nombre_achats')
	).join(Produits_Culturels, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels) \
	.filter(
		Posseder_C.pseudo == user,
		Produits_Culturels.nom_types_media.in_(idtype)
	).group_by(
		Posseder_C.pseudo,
		'annee'
	).subquery()

	# Sous-requête pour obtenir le nombre de produits limités
	subquery_produits_limite = session.query(
		Posseder_C.pseudo,
		func.sum(case((Posseder_C.limite == True, 1), else_=0)).label('nombre_produits_limite')
	).join(Produits_Culturels, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels) \
		.filter(
		Posseder_C.pseudo == user,
		Produits_Culturels.nom_types_media.in_(idtype)
	).group_by(
		Posseder_C.pseudo
	).subquery()

	# Sous-requête pour obtenir le nombre de produits collector
	subquery_produits_collector = session.query(
		Posseder_C.pseudo,
		func.sum(case((Posseder_C.collector == True, 1), else_=0)).label('nombre_produits_collector')
	).join(Produits_Culturels, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels) \
		.filter(
		Posseder_C.pseudo == user,
		Produits_Culturels.nom_types_media.in_(idtype)
	).group_by(
		Posseder_C.pseudo
	).subquery()

	subquery_achats_format = session.query(
		subquery_produits_par_annee.c.pseudo,
		func.json_object_agg(subquery_produits_par_annee.c.annee, subquery_produits_par_annee.c.nombre_achats).label(
			'achats_par_an')
	).group_by(
		subquery_produits_par_annee.c.pseudo
	).subquery()

	# Sous-requête pour obtenir la note moyenne par utilisateur
	subquery_note_moyenne = session.query(
		Notes.pseudo,
		func.avg(Notes.note).label('note_moyenne')
	).join(Fiches, Notes.id_fiches == Fiches.id_fiches) \
	.join(Produits_Culturels, Fiches.id_fiches == Produits_Culturels.id_fiches) \
	.filter(
		Notes.pseudo == user,
		Produits_Culturels.nom_types_media.in_(idtype)
	).group_by(Notes.pseudo).subquery()


	# Sous-requête pour obtenir la note médiane par utilisateur
	# SQLAlchemy ne propose pas de fonction 'median', on prend donc la 50ème percentile
	subquery_note_mediane = session.query(
		Notes.pseudo,
		func.percentile_cont(0.5).within_group(Notes.note).label('note_mediane')
	).join(Fiches, Notes.id_fiches == Fiches.id_fiches) \
		.join(Produits_Culturels, Fiches.id_fiches == Produits_Culturels.id_fiches) \
		.filter(
		Notes.pseudo == user,
		Produits_Culturels.nom_types_media.in_(idtype)
	).group_by(Notes.pseudo).subquery()

	# Sous-requêtes pour la répartition des notes de l'utilisateur
	subquery_repartition_notes = []
	for i in range(11):  # 0 à 10
		sub = session.query(
			Notes.pseudo,
			(func.sum(case((Notes.note == i, 1), else_=0)) / func.coalesce(
				func.sum(case((Notes.note != None, 1), else_=0)), 1).cast(Float)).label(
				f"proportion_note_{i}")
		).join(Fiches, Notes.id_fiches == Fiches.id_fiches) \
			.join(Produits_Culturels, Fiches.id_fiches == Produits_Culturels.id_fiches) \
			.filter(
			Notes.pseudo == user,
			Produits_Culturels.nom_types_media.in_(idtype)
		).group_by(Notes.pseudo).subquery()

		subquery_repartition_notes.append(sub)

	# Sous-requête pour les proportions de avis_popularite
	subquery_popularite_utilisateur = []
	for i in range(-1, 2):  # -1 = dislike, 0 = neutre, 1 = like
		sub = session.query(
			Avis.pseudo,
			(func.sum(case((Avis.avis_popularite == i, 1), else_=0)) / func.coalesce(
				func.sum(case((Avis.avis_popularite != None, 1), else_=0)), 1).cast(Float)).label(
				f"proportion_popularite_{i}")
		).join(Fiches, Avis.id_fiches == Fiches.id_fiches) \
			.join(Produits_Culturels, Fiches.id_fiches == Produits_Culturels.id_fiches) \
			.filter(
			Avis.pseudo == user,
			Produits_Culturels.nom_types_media.in_(idtype)
		).group_by(Avis.pseudo).subquery()

		subquery_popularite_utilisateur.append(sub)

	# Sous-requête pour les proportions de avis_cote
	subquery_cote_utilisateur = []
	for i in range(-1, 2):  # -1 = dislike, 0 = neutre, 1 = like
		sub = session.query(
			Avis.pseudo,
			(func.sum(case((Avis.avis_cote == i, 1), else_=0)) / func.coalesce(
				func.sum(case((Avis.avis_cote != None, 1), else_=0)), 1).cast(Float)).label(
				f"proportion_cote_{i}")
		).join(Fiches, Avis.id_fiches == Fiches.id_fiches) \
			.join(Produits_Culturels, Fiches.id_fiches == Produits_Culturels.id_fiches) \
			.filter(
			Avis.pseudo == user,
			Produits_Culturels.nom_types_media.in_(idtype)
		).group_by(Avis.pseudo).subquery()

		subquery_cote_utilisateur.append(sub)

	# Sous-requête pour compter les collections dans la table Posseder_T
	subquery_possession_T = session.query(
		Posseder_T.pseudo,
		func.count(Posseder_T.id_projets_transmedias).label("nombre_collections_T")
	).group_by(Posseder_T.pseudo).subquery()

	# Sous-requête pour compter le nombre total d'éléments dans chaque collection media
	subquery_total_elements_M = session.query(
		Etre_Compose.id_projets_medias,
		func.count(Etre_Compose.id_produits_culturels).label('total_elements')
	).join(Produits_Culturels, Etre_Compose.id_produits_culturels == Produits_Culturels.id_produits_culturels) \
		.filter(
		Produits_Culturels.nom_types_media.in_(idtype)
	).group_by(Etre_Compose.id_projets_medias).subquery()

	# Filtrer la table Posseder_C avant la jointure
	filtered_posseder_c = session.query(Posseder_C).join(
		Produits_Culturels, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels
	).filter(
		Posseder_C.pseudo == user,
		Produits_Culturels.nom_types_media.in_(idtype)
	).subquery()

	# Sous-requête pour compter les collections dans la table Posseder_M
	subquery_possession_M = session.query(
		Posseder_M.pseudo,
		func.count(Posseder_M.id_projets_medias).label("nombre_collections_M")
	).join(
		Projets_Medias, Posseder_M.id_projets_medias == Projets_Medias.id_projets_medias
	).filter(
		Posseder_M.pseudo == user,
		Projets_Medias.nom_types_media.in_(idtype)
	).group_by(Posseder_M.pseudo).subquery()

	# Sous-requête pour compter combien d'éléments l'utilisateur possède dans chaque collection media
	subquery_elements_possedes_M = session.query(
		filtered_posseder_c.c.pseudo,
		Etre_Compose.id_projets_medias,
		func.count(Etre_Compose.id_produits_culturels).label('elements_possedes')
	).join(
		filtered_posseder_c,
		Etre_Compose.id_produits_culturels == filtered_posseder_c.c.id_produits_culturels
	).group_by(
		filtered_posseder_c.c.pseudo,
		Etre_Compose.id_projets_medias
	).subquery()

	# Sous-requête pour compter le nombre de collections media complètes par l'utilisateur
	subquery_collections_completes_M = session.query(
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
		subquery_total_elements_M.c.total_elements
	).having(
		func.coalesce(subquery_elements_possedes_M.c.elements_possedes, 0) == subquery_total_elements_M.c.total_elements
	).subquery()

	# Sous-requête pour compter le nombre total d'éléments dans chaque collection transmedia
	subquery_total_elements_T = session.query(
		Contenir.id_projets_transmedias,
		func.count(Contenir.id_projets_medias).label('total_elements')
	).group_by(Contenir.id_projets_transmedias).subquery()


	# Sous-requête pour compter combien d'éléments l'utilisateur possède dans chaque collection transmedia
	subquery_elements_possedes_T = session.query(
		Posseder_M.pseudo,
		Contenir.id_projets_transmedias,
		func.count(Contenir.id_projets_medias).label('elements_possedes')
	).join(
		Posseder_M,
		and_(
			Contenir.id_projets_medias == Posseder_M.id_projets_medias,
			Posseder_M.pseudo == user
		)
	).group_by(Posseder_M.pseudo, Contenir.id_projets_transmedias).subquery()

	# Sous-Requête principale pour compter le nombre de collections complètes pour chaque utilisateur
	subquery_collections_completes_T = session.query(
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
		subquery_total_elements_T.c.total_elements
	).having(
		func.coalesce(subquery_elements_possedes_T.c.elements_possedes, 0) == subquery_total_elements_T.c.total_elements
	).subquery()

	# Étape 1 et 2
	subquery_user_genre_notes = session.query(
		Notes.pseudo,
		Etre_Defini.nom_genres,
		Notes.note
	).join(
		Produits_Culturels, Etre_Defini.id_produits_culturels == Produits_Culturels.id_produits_culturels
	).join(
		Notes, Produits_Culturels.id_fiches == Notes.id_fiches
	).filter(
		Notes.pseudo == user,
		Produits_Culturels.nom_types_media.in_(idtype)  # Filtrage par type de média
	).subquery()

	# Étape 3
	subquery_avg_genre_note = session.query(
		subquery_user_genre_notes.c.nom_genres,
		func.avg(subquery_user_genre_notes.c.note).label('avg_genre_note')
	).group_by(
		subquery_user_genre_notes.c.nom_genres
	).subquery()

	subquery_top_10_genre = session.query(
		subquery_avg_genre_note.c.nom_genres,
		subquery_avg_genre_note.c.avg_genre_note
	).order_by(
		desc(subquery_avg_genre_note.c.avg_genre_note)
	).limit(10).subquery()

	subquery_top_10_genre_json = session.query(
		func.json_object_agg(
			func.coalesce(subquery_top_10_genre.c.nom_genres, 'Vide'),
			func.coalesce(subquery_top_10_genre.c.avg_genre_note, 0)
		).label("top_10_genre_note")
	).subquery()

	# Sous-requête pour obtenir le nombre de produits possédés par chaque utilisateur
	subquery_nb_produits = session.query(
		Posseder_C.pseudo,
		func.coalesce(func.count(Posseder_C.id_produits_culturels), 0).label('nombre_produits')
	).join(
		Produits_Culturels, Posseder_C.id_produits_culturels == Produits_Culturels.id_produits_culturels
	).filter(
		Produits_Culturels.nom_types_media.in_(idtype)  # Filtrage par type de média
	).group_by(
		Posseder_C.pseudo
	).subquery('subquery_nb_produits')

	# Sous-requête pour obtenir le nombre total d'utilisateurs
	subquery_total_users = session.query(
		func.count().label('total_users')
	).select_from(Utilisateurs).subquery('subquery_total_users')

	# Sous-requête pour obtenir le classement de l'utilisateur
	subquery_user_rank = session.query(
		literal('user_rank').label('name'),
		func.count().label('user_rank')
	).select_from(subquery_nb_produits).filter(
		subquery_nb_produits.c.nombre_produits >= case(((session.query(subquery_nb_produits.c.nombre_produits)
		.filter(subquery_nb_produits.c.pseudo == user)
		.scalar() != None, session.query(subquery_nb_produits.c.nombre_produits)
		.filter(subquery_nb_produits.c.pseudo == user).scalar())),  else_=0))\
		.subquery('subquery_user_rank')

	# Sous-requête pour obtenir le pourcentage de l'utilisateur
	user_percentage = (subquery_user_rank.c.user_rank / subquery_total_users.c.total_users * 100).label('user_percentage')


	# Requête principale
	utilisateur = session.query(
		func.coalesce(subquery_possession.c.nombre_possessions, 0).label("nombre_possessions"),
		func.coalesce(subquery_produits_limite.c.nombre_produits_limite, 0).label("nombre_produits_limite"),
		func.coalesce(subquery_produits_collector.c.nombre_produits_collector, 0).label("nombre_produits_collector"),
		func.coalesce(subquery_achats_format.c.achats_par_an, '{}').label("achats_par_an"),
		func.coalesce(subquery_note_moyenne.c.note_moyenne, 0).label("note_moyenne"),
		func.coalesce(subquery_note_mediane.c.note_mediane, 0).label("note_mediane"),
		*[func.coalesce(sub.c[f"proportion_note_{i}"], 0).label(f"proportion_note_{i}") for i, sub in enumerate(subquery_repartition_notes)],
		*[func.coalesce(sub.c[f"proportion_popularite_{i - 1}"], 0).label(f"proportion_popularite_{i - 1}") for i, sub in enumerate(subquery_popularite_utilisateur)],
		*[func.coalesce(sub.c[f"proportion_cote_{i - 1}"], 0).label(f"proportion_cote_{i - 1}") for i, sub in enumerate(subquery_cote_utilisateur)],
		(func.coalesce(subquery_possession_T.c.nombre_collections_T, 0) + func.coalesce(subquery_possession_M.c.nombre_collections_M, 0)).label("nombre_total_collections"),
		(func.coalesce(subquery_collections_completes_M.c.nombre_collections_completes_M, 0 ) + func.coalesce(subquery_collections_completes_T.c.nombre_collections_completes_T, 0)).label("nombre_collections_completes"),
		func.coalesce(subquery_top_10_genre_json.c.top_10_genre_note, '{}').label("top_10_genre_note"),
		func.coalesce(subquery_user_rank.c.user_rank, 0).label("classement"),
		user_percentage.label("pourcentage"),



	).select_from(
		Utilisateurs,
	).outerjoin(
		subquery_achats_format,
		subquery_achats_format.c.pseudo == user
	).outerjoin(
		subquery_note_moyenne,
		subquery_note_moyenne.c.pseudo == user
	).outerjoin(
		subquery_note_mediane,
		subquery_note_mediane.c.pseudo == user
	).outerjoin(
		subquery_produits_collector,
		subquery_produits_collector.c.pseudo == user
	).outerjoin(
		subquery_produits_limite,
		subquery_produits_limite.c.pseudo == user
	).outerjoin(
		subquery_collections_completes_T,
		subquery_collections_completes_T.c.pseudo == user
	).outerjoin(
		subquery_collections_completes_M,
		subquery_collections_completes_M.c.pseudo == user
	).outerjoin(
		subquery_possession_T,
		subquery_possession_T.c.pseudo == user
	).outerjoin(
		subquery_possession_M,
		subquery_possession_M.c.pseudo == user
	)

	# Ajout de chaque sous-requête de popularite et cote en tant qu'outerjoin distinct
	for sub in subquery_popularite_utilisateur:
		utilisateur = utilisateur.outerjoin(
			sub, sub.c.pseudo == user
		)

	for sub in subquery_cote_utilisateur:
		utilisateur = utilisateur.outerjoin(
			sub, sub.c.pseudo == user
		)

	for sub in subquery_repartition_notes:
		utilisateur = utilisateur.outerjoin(
			sub, sub.c.pseudo == user
		)

	utilisateur = utilisateur.filter(
		Utilisateurs.desactive == False,
		Utilisateurs.verifie == True,
		Utilisateurs.profil_public == True
	).first()

	return utilisateur


def stats(session, user, client, idtype):
	verify_jwt_in_request(optional=True)
	cuser = None
	if current_user.is_authenticated or get_jwt_identity() is not None:
		if current_user.is_authenticated:
			cuser = current_user.pseudo
		else:
			cuser = get_jwt_identity()

	if session.query(Utilisateurs.pseudo).filter(Utilisateurs.pseudo == user, Utilisateurs.profil_public == False).scalar() and cuser != user:
		make_response(jsonify({"error": "Ce profil est privé, si vous êtes le propriétaire de ce compte, connectez-vous"}), 403)

	else:

		stats = get_user_data(user, session, idtype)
		if stats is None:
			return make_response(jsonify({"error": "Ce profil n'existe pas"}), 404)

		reponse = {
				"stats": {column: getattr(stats, column) for column in stats._fields},
			}

		if client == 'app':
			return jsonify(reponse)
		else:
			return render_template("public/user_stats.html", **reponse)
