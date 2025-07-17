import os
import subprocess
from flask import Blueprint, request, jsonify
from config import PASSWORD_STORE_DIR
from utils.filesystem import sanitize_filepath_input

decrypt_bp = Blueprint('decrypt', __name__)

@decrypt_bp.route("/api/decrypt", methods=["POST"])
def decrypt_password():
    data = request.get_json()
    filepath = data.get("filepath")
    passphrase = data.get("passphrase")

    if not filepath or not passphrase:
        return jsonify({"error": "File path and passphrase are required."}), 400

    clean_filepath = sanitize_filepath_input(filepath)
    full_path = os.path.join(PASSWORD_STORE_DIR, clean_filepath + ".gpg")
    full_path = os.path.abspath(full_path)

    if not full_path.startswith(PASSWORD_STORE_DIR + os.sep) or not os.path.isfile(full_path):
        return jsonify({"error": "Invalid file path."}), 403

    try:
        # Kill any gpg-agent instance to ensure no cached passphrase is used
        subprocess.run(["gpgconf", "--kill", "gpg-agent"], check=True)

        # Run GPG decryption using provided passphrase (not cache)
        result = subprocess.run(
            [
                "gpg",
                "--batch",
                "--yes",
                "--no-tty",
                "--pinentry-mode", "loopback",
                "--passphrase-fd", "0",
                "--decrypt", full_path
            ],
            input=passphrase.encode(),
            capture_output=True,
            check=True
        )

        return jsonify({"success": True, "content": result.stdout.decode().strip()})

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode().lower()
        if "decryption failed" in stderr or "bad passphrase" in stderr:
            return jsonify({"success": False, "error": "Incorrect passphrase. Please try again."}), 401
        elif "no secret key" in stderr:
            return jsonify({"success": False, "error": "Missing secret key for this file. Make sure your GPG key is available on the server."}), 500
        else:
            return jsonify({"success": False, "error": "Decryption failed due to an unexpected error."}), 500

    except Exception:
        return jsonify({"success": False, "error": "Unexpected server error occurred during decryption."}), 500

