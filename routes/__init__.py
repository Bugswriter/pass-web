from .tree import tree_bp
from .decrypt import decrypt_bp
from .search import search_bp

def register_routes(app):
    app.register_blueprint(tree_bp)
    app.register_blueprint(decrypt_bp)
    app.register_blueprint(search_bp)
