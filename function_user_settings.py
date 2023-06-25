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
import pyotp
import pyqrcode
import io
from base64 import b64encode
import config
def create_qr(otp_secret, user):
	qr = pyqrcode.create(pyotp.totp.TOTP(otp_secret).provisioning_uri(user, issuer_name="Geek Compagnon"))
	qr_image = io.BytesIO()
	qr.png(qr_image, scale=5)
	qr_image.seek(0)
	return qr_image
def settings(session, user, client):

	max_files = config.DROPZONE_MAX_FILES
	max_file_size = config.DROPZONE_MAX_FILE_SIZE
	accepted_files = config.DROPZONE_ALLOWED_FILE_TYPE
	default_message = config.DROPZONE_DEFAULT_MESSAGE
	qr = None
	blob = None
	result = session.query(Utilisateurs).filter(Utilisateurs.pseudo == user.pseudo).first()
	if not result or result.desactive:
		return make_response(jsonify({'error': 'Utilisateur inconnu'}), 404)

	if result.otp_secret is not None:
		qr = create_qr(result.otp_secret, result.pseudo)
		blob = b64encode(qr.getvalue()).decode()
	user_dict = {
		'pseudo': result.pseudo,
		'url_image': result.url_image,
		'notification': result.notification,
		'date_creation': result.date_creation,
		'profil_public': result.profil_public,
		'adulte': result.adulte,
		'biographie': result.biographie,
		'otp_enabled': result.otp_secret is not None,  # Add this line
		'otp_secret_qr': blob
	}
	if client == 'app':
		return make_response(jsonify(user_dict), 200)
	else:
		return render_template('public/settings.html', user=user_dict, client=client, qr=blob, max_files=max_files, max_file_size=max_file_size, accepted_files=accepted_files, default_message=default_message)
