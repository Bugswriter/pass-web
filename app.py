from flask import Flask
from config import PASSWORD_STORE_DIR
from routes import register_routes
import os

app = Flask(__name__)

# Check if password store exists
if not os.path.isdir(PASSWORD_STORE_DIR):
    print(f"Error: Password store not found at {PASSWORD_STORE_DIR}")
    exit(1)

# Register routes from modules
register_routes(app)

if __name__ == "__main__":
    app.run(debug=False, host='127.0.0.1', port=5000)
