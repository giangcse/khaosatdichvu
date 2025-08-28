import os
try:
    # New app factory
    from app import create_app
    app = create_app()
except Exception:
    # Fallback to legacy app object in main.py
    from main import app

# Load config class based on ENV var
cfg = os.getenv("FLASK_CONFIG", "ProductionConfig")
try:
    from config import ProductionConfig, DevelopmentConfig
    app.config.from_object(DevelopmentConfig if cfg == "DevelopmentConfig" else ProductionConfig)
except Exception:
    pass

# Expose Flask app object for WSGI servers (e.g. waitress, gunicorn)
# Usage:
#   waitress-serve --listen=0.0.0.0:8000 wsgi:app


