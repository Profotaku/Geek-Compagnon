class Config:
    DEBUG = True,  # some Flask specific configs
    CACHE_TYPE = "SimpleCache"  # Flask-Caching related configs
    CACHE_DEFAULT_TIMEOUT = 86400  # 24 hours cache timeout
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://claire:XR9V9vAwXX@192.168.1.9:5432/gk'