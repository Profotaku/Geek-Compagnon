import sqlalchemy as sa
from sqlalchemy import orm
Base = sa.orm.declarative_base()
import datetime
from flask_login import UserMixin
class Utilisateurs(Base, UserMixin):
    __tablename__ = 'utilisateurs'
    pseudo = sa.Column(sa.String, primary_key=True, nullable=False)
    hash_mail = sa.Column(sa.String, unique=True, nullable=False)
    hash_mdp = sa.Column(sa.String, nullable=False)
    url_image = sa.Column(sa.String, nullable=False, default='/static/images/default-profile.png')
    experience = sa.Column(sa.Integer, nullable=False, default=0)
    notification = sa.Column(sa.Boolean, nullable=False, default=False)
    date_creation = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    admin = sa.Column(sa.Boolean, nullable=False, default=False)
    fondateur = sa.Column(sa.Boolean, nullable=False, default=False)
    desactive = sa.Column(sa.Boolean, nullable=False, default=False)
    verifie = sa.Column(sa.Boolean, nullable=False, default=False)
    otp_secret = sa.Column(sa.String, nullable=True)
    profil_public = sa.Column(sa.Boolean, nullable=False, default=True)
    adulte = sa.Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"Utilisateurs('{self.pseudo}')"
    def get_id(self):
        return self.pseudo

class Types_Media(Base):
    __tablename__ = 'types_media'
    nom_types_media = sa.Column(sa.Integer, primary_key=True, nullable=False)

    def __repr__(self):
        return f"Types_Media('{self.nom_types_media}')"

class Notes(Base):
    __tablename__ = 'notes'
    id_notes = sa.Column(sa.Integer, primary_key=True, nullable=False)
    note_0 = sa.Column(sa.Integer, nullable=False, default=0)
    note_1 = sa.Column(sa.Integer, nullable=False, default=0)
    note_2 = sa.Column(sa.Integer, nullable=False, default=0)
    note_3 = sa.Column(sa.Integer, nullable=False, default=0)
    note_4 = sa.Column(sa.Integer, nullable=False, default=0)
    note_5 = sa.Column(sa.Integer, nullable=False, default=0)
    note_6 = sa.Column(sa.Integer, nullable=False, default=0)
    note_7 = sa.Column(sa.Integer, nullable=False, default=0)
    note_8 = sa.Column(sa.Integer, nullable=False, default=0)
    note_9 = sa.Column(sa.Integer, nullable=False, default=0)
    note_10 = sa.Column(sa.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Notes('{self.id_notes}')"

class Fiches(Base):
    __tablename__ = 'fiches'
    id_fiches = sa.Column(sa.Integer, primary_key=True, nullable=False)
    nom = sa.Column(sa.String, nullable=False)
    synopsis = sa.Column(sa.String, nullable=False, default='TBA')
    cmpt_favori = sa.Column(sa.Integer, nullable=False, default=0)
    consultation = sa.Column(sa.Integer, nullable=False, default=0)
    contributeur = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), nullable=False)
    url_image = sa.Column(sa.String, nullable=False, default='/static/images/fiches/default.png')
    adulte = sa.Column(sa.Boolean, nullable=False, default=False)
    info = sa.Column(sa.String, nullable=False, default='')
    concepteur = sa.Column(sa.String, nullable=False, default='')

    def __repr__(self):
        return f"Fiches('{self.nom}+{self.synopsis}')"

class Succes(Base):
    __tablename__ = 'succes'
    titre = sa.Column(sa.String, primary_key=True, nullable=False)
    description = sa.Column(sa.String, nullable=False)
    url_image = sa.Column(sa.String, nullable=False, default='/static/images/fiches/default-success.png')

    def __repr__(self):
        return f"Succes('{self.Titre}')"

class Avis(Base):
    __tablename__ = 'avis'
    id_avis = sa.Column(sa.Integer, primary_key=True, nullable=False)
    trop_popularite = sa.Column(sa.Integer, nullable=False, default=0)
    neutre_popularite = sa.Column(sa.Integer, nullable=False, default=0)
    manque_popularite = sa.Column(sa.Integer, nullable=False, default=0)
    trop_cote = sa.Column(sa.Integer, nullable=False, default=0)
    neutre_cote = sa.Column(sa.Integer, nullable=False, default=0)
    manque_cote = sa.Column(sa.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Avis('{self.ID_Avis}')"

class Noms_Alternatifs(Base):
    __tablename__ = 'noms_alternatifs'
    nom_alternatif = sa.Column(sa.String, primary_key=True, nullable=False)

    def __repr__(self):
        return f"Noms_Alternatifs('{self.id_noms_alternatifs}')"

class EAN13(Base):
    __tablename__ = 'ean13'
    ean13 = sa.Column(sa.SMALLINT, primary_key=True, nullable=False)
    limite = sa.Column(sa.Boolean, nullable=False, default=False)
    collector = sa.Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"EAN13('{self.ean13}')"

class Genres(Base):
    __tablename__ = 'genres'
    nom_genres = sa.Column(sa.String, primary_key=True, nullable=False)

    def __repr__(self):
        return f"Genres('{self.nom_genres}')"

class Etre_Associe(Base):
    __tablename__ = 'etre_associe'
    nom_genres = sa.Column(sa.String, sa.ForeignKey('genres.nom_genres'), primary_key=True, nullable=False)
    nom_types_media = sa.Column(sa.String, sa.ForeignKey('types_media.nom_types_media'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Etre_Associes('{self.nom_genres}+{self.nom_types_media}')"

class Threads(Base):
    __tablename__ = 'threads'
    id_threads = sa.Column(sa.Integer, primary_key=True, nullable=False)
    titre = sa.Column(sa.String, nullable=False)
    date_creation = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    pseudo = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), nullable=False)

    def __repr__(self):
        return f"Threads('{self.ID_Threads}')"

class Commentaires(Base):
    __tablename__ = 'commentaires'
    id_commentaires = sa.Column(sa.Integer, primary_key=True, nullable=False)
    date_post = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    contenu = sa.Column(sa.String, nullable=False)
    spoiler = sa.Column(sa.Boolean, nullable=False, default=False)
    adulte = sa.Column(sa.Boolean, nullable=False, default=False)
    signale = sa.Column(sa.Boolean, nullable=False, default=False)
    pseudo = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), nullable=False)

    def __repr__(self):
        return f"Commentaires('{self.id_commentaires}')"

class Avoir(Base):
    __tablename__ = 'avoir'
    id_commentaires = sa.Column(sa.Integer, sa.ForeignKey('commentaires.id_commentaires'), primary_key=True, nullable=False)
    id_threads = sa.Column(sa.Integer, sa.ForeignKey('threads.id_threads'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Avoir('{self.id_commentaires}'+{self.id_threads}')"

class Produits_Culturels(Base):
    __tablename__ = 'produits_culturels'
    id_produits_culturels = sa.Column(sa.Integer, primary_key=True, nullable=False)
    date_sortie = sa.Column(sa.DateTime, nullable=True, default="01/01/1900")
    id_notes = sa.Column(sa.Integer, sa.ForeignKey('notes.id_notes'), nullable=False)
    id_avis = sa.Column(sa.Integer, sa.ForeignKey('avis.id_avis'), nullable=False)
    nom_types_media = sa.Column(sa.String, sa.ForeignKey('types_media.nom_types_media'), nullable=False)
    id_fiches = sa.Column(sa.Integer, sa.ForeignKey('fiches.id_fiches'), nullable=False)
    verifie = sa.Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"Produits_Culturels('{self.ID_Produits_Culturels}')"

class Projets_Medias(Base):
    __tablename__ = 'projets_medias'
    id_projets_medias = sa.Column(sa.Integer, primary_key=True, nullable=False)
    id_notes = sa.Column(sa.Integer, sa.ForeignKey('notes.id_notes'), nullable=False)
    id_avis = sa.Column(sa.Integer, sa.ForeignKey('avis.id_avis'), nullable=False)
    nom_types_media = sa.Column(sa.String, sa.ForeignKey('types_media.nom_types_media'), nullable=False)
    id_fiches = sa.Column(sa.Integer, sa.ForeignKey('fiches.id_fiches'), nullable=False)
    titre = sa.Column(sa.String, sa.ForeignKey('succes.titre'), nullable=False)
    verifie = sa.Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"Projets_Medias('{self.id_projets_medias}')"

class Projets_Transmedias(Base):
    __tablename__ = 'projets_transmedias'
    id_projets_transmedias = sa.Column(sa.Integer, primary_key=True, nullable=False)
    id_notes = sa.Column(sa.Integer, sa.ForeignKey('notes.id_notes'), nullable=False)
    id_avis = sa.Column(sa.Integer, sa.ForeignKey('avis.id_avis'), nullable=False)
    id_fiches = sa.Column(sa.Integer, sa.ForeignKey('fiches.id_fiches'), nullable=False)
    titre = sa.Column(sa.String, sa.ForeignKey('succes.titre'), nullable=False)
    verifie = sa.Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"Projets_Transmedias('{self.ID_Projets_Transmedias}')"

class Etre_Compose(Base):
    __tablename__ = 'etre_compose'
    id_produits_culturels = sa.Column(sa.Integer, sa.ForeignKey('produits_culturels.id_produits_culturels'), primary_key=True, nullable=False)
    id_projets_medias = sa.Column(sa.Integer, sa.ForeignKey('projets_medias.id_projets_medias'), primary_key=True, nullable=False)
    ordre = sa.Column(sa.Integer, nullable=True)
    verifie = sa.Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"Etre_Composes('{self.id_produits_culturels}'+{self.id_projets_medias}')"

class Contenir(Base):
    __tablename__ = 'contenir'
    id_projets_transmedias = sa.Column(sa.Integer, sa.ForeignKey('projets_transmedias.id_projets_transmedias'), primary_key=True, nullable=False)
    id_projets_medias = sa.Column(sa.Integer, sa.ForeignKey('projets_medias.id_projets_medias'), primary_key=True, nullable=False)
    verifie = sa.Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"Contenir('{self.id_projets_transmedias}'+{self.id_projets_medias}')"

class Nommer_T(Base):
    __tablename__ = 'nommer_t'
    id_projets_transmedias = sa.Column(sa.Integer, sa.ForeignKey('projets_transmedias.id_projets_transmedias'), primary_key=True, nullable=False)
    nom_alternatif = sa.Column(sa.String, sa.ForeignKey('noms_alternatifs.nom_alternatif'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Nommer_T('{self.id_projets_transmedias}'+{self.id_noms_alternatifs}')"

class Nommer_M(Base):
    __tablename__ = 'nommer_m'
    id_projets_medias = sa.Column(sa.Integer, sa.ForeignKey('projets_medias.id_projets_medias'), primary_key=True, nullable=False)
    nom_alternatif = sa.Column(sa.String, sa.ForeignKey('noms_alternatifs.nom_alternatif'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Nommer_M('{self.id_projets_medias}'+{self.id_noms_alternatifs}')"

class Nommer_C(Base):
    __tablename__ = 'nommer_c'
    id_produits_culturels = sa.Column(sa.Integer, sa.ForeignKey('produits_culturels.id_produits_culturels'), primary_key=True, nullable=False)
    nom_alternatif = sa.Column(sa.String, sa.ForeignKey('noms_alternatifs.nom_alternatif'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Nommer_C('{self.id_produits_culturels}'+{self.id_noms_alternatifs}')"

class Etre_Identifie(Base):
    __tablename__ = 'etre_identifie'
    id_produits_culturels = sa.Column(sa.Integer, sa.ForeignKey('produits_culturels.id_produits_culturels'), primary_key=True, nullable=False)
    ean13 = sa.Column(sa.Integer, sa.ForeignKey('ean13.ean13'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Etre_Identifie('{self.id_produits_culturels}'+{self.ean13}')"

class Etre_Defini(Base):
    __tablename__ = 'etre_defini'
    id_produits_culturels = sa.Column(sa.Integer, sa.ForeignKey('produits_culturels.id_produits_culturels'), primary_key=True, nullable=False)
    nom_genres = sa.Column(sa.String, sa.ForeignKey('genres.nom_genres'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Etre_Defini('{self.id_produits_culturels}'+{self.nom_genres}')"

class Etre_Commente_T(Base):
    __tablename__ = 'etre_comment_t'
    id_projets_transmedias = sa.Column(sa.Integer, sa.ForeignKey('projets_transmedia.id_projets_transmedias'), primary_key=True, nullable=False)
    id_commentaires = sa.Column(sa.Integer, sa.ForeignKey('commentaires.id_commentaires'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Etre_Comment_T('{self.id_projets_transmedias}'+{self.id_commentaires}')"

class Etre_Commente_M(Base):
    __tablename__ = 'etre_comment_m'
    id_projets_medias = sa.Column(sa.Integer, sa.ForeignKey('projets_medias.id_projets_medias'), primary_key=True, nullable=False)
    id_commentaires = sa.Column(sa.Integer, sa.ForeignKey('commentaires.id_commentaires'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Etre_Comment_M('{self.id_projets_medias}'+{self.id_commentaires}')"

class Etre_Commente_C(Base):
    __tablename__ = 'etre_comment_c'
    id_produits_culturels = sa.Column(sa.Integer, sa.ForeignKey('produits_culturels.id_produits_culturels'), primary_key=True, nullable=False)
    id_commentaires = sa.Column(sa.Integer, sa.ForeignKey('commentaires.id_commentaires'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Etre_Comment_C('{self.id_produits_culturels}'+{self.id_commentaires}')"

class Posseder_T(Base):
    __tablename__ = 'posseder_t'
    id_projets_transmedias = sa.Column(sa.Integer, sa.ForeignKey('projets_transmedia.id_projets_transmedias'), primary_key=True, nullable=False)
    pseudo = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), primary_key=True, nullable=False)
    favori = sa.Column(sa.Boolean, nullable=False, default=False)
    note = sa.Column(sa.SMALLINT, nullable=True)
    avis_popularite = sa.Column(sa.Boolean, nullable=True)
    avis_cote = sa.Column(sa.Boolean, nullable=True)
    date_ajout = sa.Column(sa.TIMESTAMP, nullable=False, default=datetime.datetime.now().timestamp())

    def __repr__(self):
        return f"Posseder_T('{self.id_projets_transmedias}'+{self.pseudo}')"

class Posseder_M(Base):
    __tablename__ = 'posseder_m'
    id_projets_medias = sa.Column(sa.Integer, sa.ForeignKey('projets_medias.id_projets_medias'), primary_key=True, nullable=False)
    pseudo = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), primary_key=True, nullable=False)
    favori = sa.Column(sa.Boolean, nullable=False, default=False)
    note = sa.Column(sa.SMALLINT, nullable=True)
    avis_popularite = sa.Column(sa.Boolean, nullable=True)
    avis_cote = sa.Column(sa.Boolean, nullable=True)
    date_ajout = sa.Column(sa.TIMESTAMP, nullable=False, default=datetime.datetime.now().timestamp())

    def __repr__(self):
        return f"Posseder_M('{self.id_projets_medias}'+{self.pseudo}')"

class Posseder_C(Base):
    __tablename__ = 'posseder_c'
    id_produits_culturels = sa.Column(sa.Integer, sa.ForeignKey('produits_culturels.id_produits_culturels'), primary_key=True, nullable=False)
    pseudo = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), primary_key=True, nullable=False)
    physiquement = sa.Column(sa.Boolean, nullable=False, default=True)
    favori = sa.Column(sa.Boolean, nullable=False, default=False)
    note = sa.Column(sa.SMALLINT, nullable=True)
    avis_popularite = sa.Column(sa.Boolean, nullable=True)
    avis_cote = sa.Column(sa.Boolean, nullable=True)
    souhaite = sa.Column(sa.Boolean, nullable=False, default=False)
    date_ajout = sa.Column(sa.TIMESTAMP, nullable=False, default=datetime.datetime.now().timestamp())
    limite = sa.Column(sa.Boolean, nullable=False, default=False)
    collector = sa.Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"Posseder_C('{self.id_produits_culturels}'+{self.pseudo}')"

class Moyennes(Base):
    __tablename__ = 'moyennes'
    id_moyennes = sa.Column(sa.Integer, primary_key=True, nullable=False)
    moyenne = sa.Column(sa.Float, nullable=False)
    nom_types_media = sa.Column(sa.String, sa.ForeignKey('types_media.nom_types_media'), nullable=False)

    def __repr__(self):
        return f"Moyennes('{self.id_moyennes}'+{self.moyenne}')"

class Donner(Base):
    __tablename__ = 'donner'
    pseudo = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), primary_key=True, nullable=False)
    id_moyennes = sa.Column(sa.Integer, sa.ForeignKey('moyennes.id_moyennes'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Donner('{self.pseudo}'+{self.id_moyennes}')"

class Nombre_Possessions(Base):
    __tablename__ = 'nombre_possessions'
    id_nombre_possessions = sa.Column(sa.Integer, primary_key=True, nullable=False)
    nombre_possession = sa.Column(sa.Integer, nullable=False)
    nom_types_media = sa.Column(sa.String, sa.ForeignKey('types_media.nom_types_media'), nullable=False)

    def __repr__(self):
        return f"Nombre_Possession('{self.id_nombre_possession}'+{self.nombre_possession}')"

class Avoir_Nombre_Possession(Base):
    __tablename__ = 'avoir_nombre_possession'
    pseudo = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), primary_key=True, nullable=False)
    id_nombre_possessions = sa.Column(sa.Integer, sa.ForeignKey('nombre_possessions.id_nombre_possessions'), primary_key=True, nullable=False)

    def __repr__(self):
        return f"Avoir_Nombre_Possession('{self.pseudo}'+{self.id_nombre_possession}')"

class Notes_Utilisateurs(Base):
    __tablename__ = 'notes_utilisateurs'
    id_notes = sa.Column(sa.Integer, sa.ForeignKey('notes.id_notes'), primary_key=True, nullable=False)
    pseudo = sa.Column(sa.String, sa.ForeignKey('utilisateurs.pseudo'), primary_key=True, nullable=False)
    nom_types_media = sa.Column(sa.String, sa.ForeignKey('types_media.nom_types_media'), nullable=False)

    def __repr__(self):
        return f"Notes_Utilisateurs('{self.id_notes}'+{self.pseudo}+{self.nom_types_media}')"