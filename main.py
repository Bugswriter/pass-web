import os
import subprocess
from flask import Flask, render_template, request, jsonify
import re # For path sanitization and security

app = Flask(__name__)

# --- Configuration ---
# IMPORTANT: Configure this path to your password store.
# This path should point to the root of your cloned password-store repository.
# For example, if you cloned it to /home/youruser/my-passwords, set it to that.
# os.path.expanduser("~/.local/share/password-store") is a common default.
PASSWORD_STORE_DIR = os.path.expanduser("~/.local/share/password-store")

# Ensure the path is absolute and normalized for security checks
PASSWORD_STORE_DIR = os.path.abspath(PASSWORD_STORE_DIR)
# --- End Configuration ---


# --- Helper Functions ---

def get_password_tree(base_path, current_path=""):
    """
    Recursively builds a dictionary representing the password store tree.
    It identifies directories and GPG-encrypted files,
    excluding files like README.md and hiding the .gpg extension for display.
    """
    tree = {}
    full_current_path = os.path.join(base_path, current_path)

    # Validate that the current path is indeed a directory within our base path
    # and that it is actually a directory.
    if not full_current_path.startswith(base_path) or not os.path.isdir(full_current_path):
        app.logger.error(f"Attempted to access invalid or non-directory path: {full_current_path}")
        return {} # Return empty if path is invalid or outside the base

    # Sort items for consistent display order
    for item in sorted(os.listdir(full_current_path)):
        # Skip hidden directories like .git
        if item.startswith('.'): # This will catch .git, .gnupg, etc.
            continue
        # Skip README files
        if item.lower() == "readme.md":
            continue

        item_full_path = os.path.join(full_current_path, item)
        relative_path_for_storage = os.path.join(current_path, item)

        if os.path.isdir(item_full_path):
            # If it's a directory, recursively get its contents
            tree[item] = get_password_tree(base_path, relative_path_for_storage)
        elif item.endswith(".gpg"):
            # If it's a GPG file, hide the .gpg extension for display
            display_name = item[:-4]
            # Store the full relative path to the GPG file (without .gpg extension)
            # This is the path the frontend will send for decryption
            tree[display_name] = relative_path_for_storage[:-4]

    return tree

def sanitize_filepath_input(filepath_str):
    """
    Sanitizes a user-provided filepath string by normalizing it.
    This function primarily cleans the string format; the security check
    (ensuring it's within the allowed directory) is done at the point of use.
    """
    # Normalize the path to handle sequences like 'a/../b'
    # This also converts backslashes to forward slashes on Windows if needed,
    # then normalizes.
    sanitized = os.path.normpath(filepath_str)

    # Remove any leading slashes that might have been introduced or explicitly provided
    if sanitized.startswith('/') or sanitized.startswith('\\'):
        sanitized = sanitized[1:]

    # Remove any trailing slashes if present (for consistency, though not strictly necessary for security here)
    if sanitized.endswith('/') or sanitized.endswith('\\'):
        sanitized = sanitized[:-1]

    return sanitized


# --- Flask Routes ---

@app.route('/')
def index():
    """
    Renders the main HTML page.
    The password tree is fetched by JavaScript on the client side after the page loads.
    This keeps the initial render fast and simple.
    """
    return render_template('index.html')

@app.route('/api/tree', methods=['GET'])
def get_tree_api():
    """
    API endpoint to get the full password tree.
    This is called by the frontend JavaScript.
    """
    try:
        password_tree = get_password_tree(PASSWORD_STORE_DIR)
        return jsonify({"tree": password_tree})
    except Exception as e:
        app.logger.exception("Error generating password tree:")
        return jsonify({"error": "Failed to load password tree."}), 500

@app.route('/api/decrypt', methods=['POST'])
def decrypt_password():
    """
    Decrypts a GPG file and returns its content.
    Expects 'filepath' (relative path to .gpg file, WITHOUT .gpg extension) and 'passphrase' in the POST request JSON.
    """
    data = request.get_json()
    filepath = data.get('filepath') # This 'filepath' is the relative path *without* the .gpg extension
    passphrase = data.get('passphrase')

    if not filepath or not passphrase:
        return jsonify({"error": "File path and passphrase are required."}), 400

    # Sanitize the input filepath string (e.g., remove redundant slashes, handle '..')
    clean_filepath = sanitize_filepath_input(filepath)

    # Construct the full absolute path to the GPG file
    # This assumes the clean_filepath is correctly representing a relative path
    # from the PASSWORD_STORE_DIR.
    potential_gpg_file_path = os.path.join(PASSWORD_STORE_DIR, clean_filepath + ".gpg")
    
    # Resolve the absolute path to ensure we're comparing canonical paths
    abs_potential_gpg_file_path = os.path.abspath(potential_gpg_file_path)
    abs_password_store_dir = os.path.abspath(PASSWORD_STORE_DIR)

    # CRUCIAL SECURITY CHECK:
    # 1. Ensure the resolved absolute path starts with the absolute password store directory path,
    #    and specifically that it's a child (using os.sep).
    # 2. Ensure the file actually exists on the filesystem.
    if not abs_potential_gpg_file_path.startswith(abs_password_store_dir + os.sep) or \
       not os.path.isfile(abs_potential_gpg_file_path):
        app.logger.warning(f"Attempted to access file outside password store or non-existent file: {abs_potential_gpg_file_path}")
        return jsonify({"success": False, "error": "Invalid file path or file not found."}), 403 # Forbidden

    try:
        # Use subprocess to call gpg for decryption
        # --batch: non-interactive mode, useful for scripts
        # --passphrase-fd 0: tells gpg to read the passphrase from file descriptor 0 (stdin)
        # --decrypt: performs the decryption
        process = subprocess.run(
            ['gpg', '--batch', '--passphrase-fd', '0', '--decrypt', abs_potential_gpg_file_path],
            input=passphrase.encode('utf-8'), # Pass the passphrase as bytes to stdin
            capture_output=True, # Capture stdout and stderr
            # REMOVED: text=True, as input is already bytes
            check=True # If check is True, CalledProcessError is raised for non-zero exit codes
        )
        # Decode the output after decryption as it's captured as bytes now
        decrypted_content = process.stdout.decode('utf-8').strip()
        return jsonify({"success": True, "content": decrypted_content})
    except subprocess.CalledProcessError as e:
        # Handle GPG specific errors
        app.logger.error(f"GPG decryption error for {abs_potential_gpg_file_path}: {e.stderr.decode('utf-8')}") # Decode stderr too
        if "bad passphrase" in e.stderr.decode('utf-8').lower() or "decryption failed" in e.stderr.decode('utf-8').lower():
            return jsonify({"success": False, "error": "Incorrect passphrase or decryption failed. Please check your passphrase and GPG key."}), 401
        elif "no secret key" in e.stderr.decode('utf-8').lower():
             return jsonify({"success": False, "error": "No secret key found to decrypt this file. Ensure your GPG key is imported and accessible."}), 500
        else:
            return jsonify({"success": False, "error": f"GPG error: {e.stderr.decode('utf-8')}"}), 500
    except Exception as e:
        # Catch any other unexpected errors
        app.logger.exception(f"Unexpected error during decryption of {filepath}:")
        return jsonify({"success": False, "error": "An unexpected server error occurred during decryption."}), 500

@app.route('/api/search', methods=['POST'])
def search_passwords():
    """
    Searches for password entries matching a query.
    Performs a simple case-insensitive search on the display names of files and directories.
    If the query is empty, returns the full tree.
    """
    data = request.get_json()
    query = data.get('query', '').lower()

    # Recursive function to filter the tree based on the search query
    def filter_tree(tree_node, search_query):
        filtered_node = {}
        for key, value in tree_node.items():
            if isinstance(value, dict): # It's a directory
                # Recursively filter sub-directories
                sub_filtered = filter_tree(value, search_query)
                if sub_filtered:
                    # If the directory or its contents match, include it
                    filtered_node[key] = sub_filtered
                elif search_query in key.lower():
                    # If the directory name itself matches, include the whole subtree
                    filtered_node[key] = value
            elif isinstance(value, str): # It's a file path (without .gpg extension)
                # If the file's display name matches, include it
                if search_query in key.lower():
                    filtered_node[key] = value
        return filtered_node

    try:
        full_tree = get_password_tree(PASSWORD_STORE_DIR)
        if not query:
            # If query is empty, return the full tree
            return jsonify({"tree": full_tree})
        else:
            # Otherwise, return the filtered tree
            filtered_tree = filter_tree(full_tree, query)
            return jsonify({"tree": filtered_tree})
    except Exception as e:
        app.logger.exception("Error during password search:")
        return jsonify({"error": "Failed to perform search."}), 500


# --- Application Entry Point ---
if __name__ == '__main__':
    # Initial check to ensure the password store directory exists before starting the app
    if not os.path.isdir(PASSWORD_STORE_DIR):
        print(f"Error: Password store directory not found at '{PASSWORD_STORE_DIR}'")
        print("Please ensure your password store is cloned to this location and the 'PASSWORD_STORE_DIR' variable in app.py is correctly configured.")
        exit(1) # Exit if the directory is not found

    app.run(debug=False, host='127.0.0.1', port=5000)
