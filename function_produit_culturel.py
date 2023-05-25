from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response, g
from dataclass import *
from sqlalchemy import orm, or_, and_, select, join, outerjoin, func, desc, union_all, literal, case, distinct
from config import *
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    verify_jwt_in_request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from cache import cache


@cache.memoize(timeout=24*60*60) # cache durée de 24 heures
def get_objective_data(id_produit_culturel, session):
	produit = session.query(Produits_Culturels.date_sortie, Produits_Culturels.nom_types_media, Fiches.nom, Fiches.synopsis, Fiches.contributeur, Fiches.url_image, Fiches.adulte, Fiches.info, Fiches.concepteur) \
		.join(Fiches, Produits_Culturels.id_fiches == Fiches.id_fiches) \
		.filter(Produits_Culturels.id_produits_culturels == id_produit_culturel) \
		.filter(Produits_Culturels.verifie == True).first()
	return produit


def produit_culturel_app(session, id_produit_culturel, client):
	# check if produit culturel is in database
	if not session.query(Produits_Culturels).filter_by(id_produits_culturels=id_produit_culturel, verifie=True).first():
		return jsonify({"error": "La fiche produit exigée n'est pas présente dans nos données"}), 404

	isadulte = False
	verify_jwt_in_request(optional=True)
	if current_user.is_authenticated or get_jwt_identity() is not None:
		if current_user.is_authenticated:
			user = current_user.pseudo
			isadulte = current_user.adulte
		else:
			user = get_jwt_identity()
			isadulte = session.execute(
				select(Utilisateurs.adulte).where(Utilisateurs.pseudo == get_jwt_identity())).scalar()

		info_user = session.query(Avis.favori, Avis.avis_popularite, Avis.avis_cote, Notes.note) \
			.select_from(Produits_Culturels) \
			.outerjoin(Avis, and_(Produits_Culturels.id_fiches == Avis.id_fiches, Avis.pseudo == user)) \
			.outerjoin(Notes, and_(Produits_Culturels.id_fiches == Notes.id_fiches, Notes.pseudo == user)) \
			.filter(Produits_Culturels.id_produits_culturels == id_produit_culturel).first()
	else:
		user = g.user
		isadulte = False

	# Get static data from cache
	produit = get_objective_data(id_produit_culturel, session)

	produit_is_adulte = session.execute(select(Fiches.adulte).join(Fiches).select_from(Produits_Culturels).filter(Produits_Culturels.id_fiches == Fiches.id_fiches).filter(Produits_Culturels.id_produits_culturels == id_produit_culturel))

	print(produit)
	print(info_user if hasattr(info_user, 'favori') else None)
	if isadulte or produit_is_adulte or session.get('adulte', False):
		render_template("produit_culturel.html", activate_adulte_js_verification=False, produit=produit, info_user=info_user)
	else:
		return render_template("produit_culturel.html", activate_adulte_js_verification=True, produit=produit, info_user=info_user)


