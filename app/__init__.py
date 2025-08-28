import os
from flask import Flask
from flask_cors import CORS


def create_app(config_object: str | None = None) -> Flask:
    # Phục vụ tệp tĩnh từ app/static
    base_dir = os.path.dirname(__file__)
    static_dir = os.path.join(base_dir, 'static')
    templates_dir = os.path.join(base_dir, 'templates')
    app = Flask(__name__, static_folder=static_dir, template_folder=templates_dir)

    # Load config
    cfg = config_object or os.getenv("FLASK_CONFIG", "ProductionConfig")
    try:
        from config import ProductionConfig, DevelopmentConfig
        app.config.from_object(DevelopmentConfig if cfg == "DevelopmentConfig" else ProductionConfig)
    except Exception:
        pass

    # Extensions
    CORS(app)

    # Redis client (tùy chọn)
    try:
        import redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        app.extensions["redis"] = redis.Redis.from_url(redis_url, decode_responses=True)
    except Exception:
        # Không chặn app nếu Redis chưa sẵn sàng
        app.extensions["redis"] = None

    # Blueprints
    from .routes.api import api_bp
    from .routes.public import public_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
