import os


class BaseConfig:
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PREFERRED_URL_SCHEME = "https" if os.getenv("FORCE_HTTPS", "false").lower() == "true" else "http"
    # CORS can be restricted via env, fallback to * for compatibility with current app usage
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"


