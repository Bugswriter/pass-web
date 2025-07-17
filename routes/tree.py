from flask import Blueprint, jsonify
from config import PASSWORD_STORE_DIR
from utils.filesystem import get_password_tree

tree_bp = Blueprint('tree', __name__)

@tree_bp.route("/api/tree", methods=["GET"])
def get_tree():
    try:
        tree = get_password_tree(PASSWORD_STORE_DIR)
        return jsonify({"tree": tree})
    except Exception:
        return jsonify({"error": "Failed to load password tree."}), 500
