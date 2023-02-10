from datetime import timedelta

class Config:
    DEBUG = True,  # some Flask specific configs
    CACHE_TYPE = "SimpleCache"  # Flask-Caching related configs
    CACHE_DEFAULT_TIMEOUT = 86400  # 24 hours cache timeout
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://claire:XR9V9vAwXX@192.168.1.9:5432/gk'
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    SECRET_KEY = 'ZSgmA*4FS*%e$Y69tgb!^mb7q'
    JWT_SECRET = 'ZSgmA*4FS*%e$Y69tgb!^mb7q'
    JWT_AUTHMAXAGE = 3600
    JWT_REFRESHMAXAGE = 604800
    JWT_ISSUER = "Geek-Compagnon"
    JWT_AUTHTYPE = "HS256"
    WTF_CSRF_SECRET_KEY = '&8mN%Ux%38#RC788^a2cDJL!L'
