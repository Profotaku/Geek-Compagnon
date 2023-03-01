from datetime import timedelta


DEBUG = True,  # some Flask specific configs
CACHE_TYPE = "SimpleCache"  # Flask-Caching related configs
CACHE_DEFAULT_TIMEOUT = 86400  # 24 hours cache timeout
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'postgresql://claire:XR9V9vAwXX@192.168.1.9:5432/gk'
REMEMBER_COOKIE_DURATION = timedelta(days=30)
SECRET_KEY = 'ZSgmA*4FS*%e$Y69tgb!^mb7q'
SECRET_KEY_SALT = 'q$%m*#C873m9o9$TAYmPXbf6k$#Ls@@C735$^'
JWT_SECRET = 'ZSgmA*4FS*%e$Y69tgb!^mb7q'
JWT_AUTHMAXAGE = 3600
JWT_REFRESHMAXAGE = 604800
JWT_ISSUER = "Geek-Compagnon"
JWT_AUTHTYPE = "HS256"
WTF_CSRF_SECRET_KEY = '&8mN%Ux%38#RC788^a2cDJL!L',
JSON_AS_ASCII = False
SESSION_TYPE = 'filesystem'
SESSION_FILE_THRESHOLD = 500
JWT_SESSION_COOKIE = False
MAILJET_API_KEY = '2d3be8f255e5540a0cbd92caa1fe0fe9' # not the real key
MAILJET_API_SECRET = 'efe3cd09bf3e40b93a181de471119033' # not the real key
BCRYPT_UNIQUE_SALT = "$2b$12$43FaaT4owS0eDO2AbEpsn." # not the real salt
DROPZONE_ALLOWED_FILE_CUSTOM = True
DROPZONE_ALLOWED_FILE_TYPE = '.png, .jpg, .jpeg'
DROPZONE_MAX_FILES = 1
DROPZONE_DEFAULT_MESSAGE = "Glissez-déposez vos fichiers ici ou cliquez pour les sélectionner"
DROPZONE_INVALID_FILE_TYPE = "Vous ne pouvez pas envoyer ce type de fichier, seuls les images jpg, jpeg et png sont acceptés"
DROPZONE_FILE_TOO_BIG = "Le fichier est trop gros: ({{filesize}}Mo). Taille max: {{maxFilesize}}Mo."
DROPZONE_SERVER_ERROR = "Une erreur est survenue lors de l'envoi du fichier: {{statusCode}}"
DROPZONE_BROWSER_UNSUPPORTED = "Votre navigateur n'est pas compatible avec le glisser-déposer"
DROPZONE_MAX_FILE_EXCEED = "Vous ne pouvez pas envoyer plus de {{maxFiles}} fichiers"
DROPZONE_ENABLE_CSRF = True

class Image_Signature:
    JPEG = b'\xff\xd8'
    PNG = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'

    def __iter__(self):
        # renvoie une liste des attributs de classe de la classe
        return ((attr, getattr(self, attr)) for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__"))