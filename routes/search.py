from flask import Blueprint, request, jsonify
from config import PASSWORD_STORE_DIR
from utils.filesystem import get_password_tree

search_bp = Blueprint('search', __name__)

@search_bp.route("/api/search", methods=["POST"])
def search_passwords():
    query = request.get_json().get("query", "").lower()

    def filter_tree(tree, search):
        result = {}
        for key, value in tree.items():
            if isinstance(value, dict):
                sub = filter_tree(value, search)
                if sub or search in key.lower():
                    result[key] = sub or value
            elif search in key.lower():
                result[key] = value
        return result

    try:
        full_tree = get_password_tree(PASSWORD_STORE_DIR)
        return jsonify({"tree": filter_tree(full_tree, query)})
    except Exception:
        return jsonify({"error": "Search failed"}), 500
