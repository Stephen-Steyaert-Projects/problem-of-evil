from flask import Flask, url_for as flask_url_for, send_from_directory, request
from flask_caching import Cache
from flask_compress import Compress
from site_blueprints import blueprint
from os import environ
from pathlib import Path

app = Flask(__name__)

# Enable gzip compression
Compress(app)

# Read secret key from Docker secret or environment variable
def get_secret(secret_name, env_var=None, default=None):
    """Read secret from Docker secret file or environment variable."""
    secret_path = Path(f'/run/secrets/{secret_name}')
    if secret_path.exists():
        return secret_path.read_text().strip()
    if env_var and environ.get(env_var):
        return environ.get(env_var)
    return default

app.config['SECRET_KEY'] = get_secret('flask_secret_key', 'SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure caching - short timeout in dev, longer in production
is_production = environ.get('FLASK_ENV') == 'production'
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',  # In-memory cache
    'CACHE_DEFAULT_TIMEOUT': 3600 if is_production else 60  # 1 hour in prod, 1 minute in dev
})

# Automatic cache busting for static files
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    """Add file modification timestamp to static file URLs for cache busting."""
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = Path(app.root_path) / 'static' / filename
            if file_path.exists():
                values['v'] = int(file_path.stat().st_mtime)
    return flask_url_for(endpoint, **values)

# Make request available in all templates
@app.context_processor
def inject_request():
    """Make request object available in all templates."""
    return dict(request=request)

# Add HTTP cache headers for static files
@app.after_request
def add_cache_headers(response):
    """Add cache control headers for static files."""
    if request.path.startswith('/static/'):
        # Cache static files for 1 year (immutable due to cache busting)
        response.cache_control.max_age = 31_536_000
        response.cache_control.public = True
        response.cache_control.immutable = True
    return response

# Route for robots.txt
@app.route('/robots.txt')
def robots():
    return send_from_directory(Path(app.root_path) / 'static', 'robots.txt')

# Route for sitemap.xml
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(Path(app.root_path) / 'static', 'sitemap.xml')

# Register blueprints
app.register_blueprint(blueprint, url_prefix="")

# Initialize cache in blueprint
from site_blueprints import init_cache
init_cache(cache)

if __name__ == "__main__":
    # This only runs when executing `python main.py` directly (development)
    # In production, gunicorn imports the app directly
    debug = environ.get('FLASK_ENV') != 'production'
    app.run(
        host='0.0.0.0',
        port=int(environ.get('PORT', 5001)),
        debug=debug
    )