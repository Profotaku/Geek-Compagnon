from flask import jsonify
from sqlalchemy import select, func, and_, or_, desc
from dataclass import *
def search(title, isadulte, session):
    result_culturel = session.execute(
        select(Produits_Culturels.id_produits_culturels, Fiches.nom, Fiches.synopsis, Produits_Culturels.date_sortie,
               Produits_Culturels.nom_types_media, Fiches.url_image, Fiches.adulte, Noms_Alternatifs.nom_alternatif,
               Etre_Compose.ordre, Projets_Medias.id_projets_medias,
               func.similarity(Fiches.nom, title).label('similarity_nom'),
               func.similarity(Noms_Alternatifs.nom_alternatif, title).label('similarity_alt')) \
        .select_from(Produits_Culturels) \
        .join(Fiches, Fiches.id_fiches == Produits_Culturels.id_fiches) \
        .join(Types_Media, Types_Media.nom_types_media == Produits_Culturels.nom_types_media) \
        .outerjoin(Nommer_C, Nommer_C.id_produits_culturels == Produits_Culturels.id_produits_culturels) \
        .outerjoin(Noms_Alternatifs, Noms_Alternatifs.nom_alternatif == Nommer_C.nom_alternatif) \
        .outerjoin(Etre_Compose, and_(Etre_Compose.id_produits_culturels == Produits_Culturels.id_produits_culturels,
                                      Etre_Compose.verifie == True)) \
        .outerjoin(Projets_Medias, Projets_Medias.id_projets_medias == Etre_Compose.id_projets_medias) \
        .filter(or_(func.similarity(Fiches.nom, title) > 0.3,
                    func.similarity(Noms_Alternatifs.nom_alternatif, title) > 0.3)) \
        .filter(Produits_Culturels.verifie == True) \
        .distinct(Produits_Culturels.id_produits_culturels) \
        .order_by(Produits_Culturels.id_produits_culturels, desc('similarity_nom'), desc('similarity_alt')) \
        .limit(4)) \
        .all()
    i = 0
    for row in result_culturel:
        i = i + 1
        if row.id_projets_medias is not None:
            result_projet = session.execute(select(Fiches.nom)
                                            .select_from(Fiches).
                                            join(Projets_Medias, Projets_Medias.id_fiches == Fiches.id_fiches)
                                            .filter(Projets_Medias.id_projets_medias == row.id_projets_medias)) \
                .fetchone()
            row_as_dict = row._asdict()
            if result_projet is not None:
                row_as_dict['nom_projet'] = result_projet.nom
            result_culturel[i - 1] = row_as_dict
        else:
            result_culturel[i - 1] = row._asdict()

    result_media = session.execute(
        select(Projets_Medias.id_projets_medias, Fiches.nom, Fiches.synopsis, Fiches.url_image, Fiches.adulte,
               Noms_Alternatifs.nom_alternatif, Projets_Medias.nom_types_media,
               Projets_Transmedias.id_projets_transmedias, func.similarity(Fiches.nom, title).label('similarity_nom'),
               func.similarity(Noms_Alternatifs.nom_alternatif, title).label('similarity_alt')) \
        .select_from(Projets_Medias) \
        .join(Fiches, Fiches.id_fiches == Projets_Medias.id_fiches) \
        .join(Types_Media, Types_Media.nom_types_media == Projets_Medias.nom_types_media) \
        .outerjoin(Nommer_M, Nommer_M.id_projets_medias == Projets_Medias.id_projets_medias) \
        .outerjoin(Noms_Alternatifs, Noms_Alternatifs.nom_alternatif == Nommer_M.nom_alternatif) \
        .outerjoin(Contenir,
                   and_(Contenir.id_projets_medias == Projets_Medias.id_projets_medias, Contenir.verifie == True)) \
        .outerjoin(Projets_Transmedias, Projets_Transmedias.id_projets_transmedias == Contenir.id_projets_transmedias) \
        .filter(or_(func.similarity(Fiches.nom, title) > 0.3,
                    func.similarity(Noms_Alternatifs.nom_alternatif, title) > 0.3)) \
        .filter(Projets_Medias.verifie == True) \
        .distinct(Projets_Medias.id_projets_medias) \
        .order_by(Projets_Medias.id_projets_medias, desc('similarity_nom'), desc('similarity_alt')) \
        .limit(4)) \
        .all()
    i = 0
    for row in result_media:
        i = i + 1
        if row.id_projets_transmedias is not None:
            result_projet = session.execute(select(Fiches.nom)
                                            .select_from(Fiches)
                                            .join(Projets_Transmedias,
                                                  Projets_Transmedias.id_fiches == Fiches.id_fiches)
                                            .filter(
                Projets_Transmedias.id_projets_transmedias == row.id_projets_transmedias)) \
                .fetchone()
            row_as_dict = row._asdict()
            if result_projet is not None:
                row_as_dict['nom_transmedia'] = result_projet.nom
            result_media[i - 1] = row_as_dict
        else:
            result_media[i - 1] = row._asdict()

    result_transmedia = session.execute(
        select(Projets_Transmedias.id_projets_transmedias, Fiches.nom, Fiches.synopsis, Fiches.url_image, Fiches.adulte,
               Noms_Alternatifs.nom_alternatif, func.similarity(Fiches.nom, title).label('similarity_nom'),
               func.similarity(Noms_Alternatifs.nom_alternatif, title).label('similarity_alt')) \
        .select_from(Projets_Transmedias) \
        .join(Fiches, Fiches.id_fiches == Projets_Transmedias.id_fiches) \
        .outerjoin(Nommer_T, Nommer_T.id_projets_transmedias == Projets_Transmedias.id_projets_transmedias) \
        .outerjoin(Noms_Alternatifs, Noms_Alternatifs.nom_alternatif == Nommer_T.nom_alternatif) \
        .filter(or_(func.similarity(Fiches.nom, title) > 0.3,
                    func.similarity(Noms_Alternatifs.nom_alternatif, title) > 0.3)) \
        .filter(Projets_Transmedias.verifie == True) \
        .distinct(Projets_Transmedias.id_projets_transmedias) \
        .order_by(Projets_Transmedias.id_projets_transmedias, desc('similarity_nom'), desc('similarity_alt')) \
        .limit(4)) \
        .all()
    i = 0
    for row in result_transmedia:
        i = i + 1
        result_transmedia[i - 1] = row._asdict()
    if not isadulte:
        result_culturel = [row for row in result_culturel if row['adulte'] == False]
        result_media = [row for row in result_media if row['adulte'] == False]
        result_transmedia = [row for row in result_transmedia if row['adulte'] == False]
    return jsonify(
        {
            'result_culturel': [dict(row) for row in result_culturel],
            'result_media': [dict(row) for row in result_media],
            'result_transmedia': [dict(row) for row in result_transmedia],
        }
    )