# Password Store Web Interface

A minimal and simple Flask application that provides a web interface to browse, search, and decrypt entries from your GPG-encrypted password store (`pass`).

## Description

This project allows you to access your GPG-encrypted passwords through a web browser. It scans your `pass` compatible directory structure, presents it as a browsable tree, and enables you to decrypt individual password entries by providing your GPG passphrase. The decrypted content is displayed temporarily in a modal window.

## Features

* **Tree View:** Browse your password store hierarchy in an intuitive tree structure.

* **Search Functionality:** Quickly find password entries using a real-time search filter.

* **On-Demand Decryption:** Decrypt individual `.gpg` password files by entering your GPG passphrase in the web interface.

* **Copy to Clipboard:** Easily copy decrypted password content to your clipboard.

* **Minimalist Design:** Clean and responsive user interface built with Tailwind CSS.

* **Security Focused (for local use):** Passphrases are not stored by the application and are used only for the immediate decryption operation.

## **Security Disclaimer: IMPORTANT!**

This application is designed for **personal, local network, or secure server use only**. **It is NOT intended for public internet deployment without significant additional security measures**, including but not limited to:

* Robust user authentication and authorization (beyond basic GPG key presence).

* Always serving over HTTPS.

* Comprehensive input validation and sanitization.

* Regular security audits.

Exposing this application to the internet without proper safeguards could compromise your entire password store. Use with extreme caution and only in environments where you control access.

## Prerequisites

Before running this application, ensure you have the following installed and configured:

1.  **Python 3.x:**

    ```
    python --version
    ```

2.  **Flask:** A Python web framework.

3.  **GnuPG (`gpg`):** The GNU Privacy Guard, for handling GPG encryption/decryption.

    ```
    gpg --version
    ```

4.  **Your GPG Private Key:** The private key used to encrypt your password store entries must be imported into the GPG keyring of the user account that will run this Flask application.
    You can list your keys with:

    ```
    gpg --list-keys
    gpg --list-secret-keys
    ```

    Ensure the key corresponding to your password store is present.

5.  **Your Password Store (`pass`):** A cloned copy of your GPG-encrypted password repository. The application expects a directory structure compatible with `pass`.

    Example structure:

    ```
    .
    ├── accounts/
    │   ├── amazon.gpg
    │   └── google.gpg
    ├── finance/
    │   └── paypal.gpg
    └── README.md
    ```

## Setup Instructions

1.  **Clone the Repository (or create the project structure):**
    If you're setting up manually, create the project directory:

    ```
    mkdir password_web_interface
    cd password_web_interface
    mkdir templates
    ```

    Then, save `app.py` in the root (`password_web_interface/`) and `index.html` in the `templates/` directory.

2.  **Set up a Python Virtual Environment (Recommended):**
    This isolates your project's dependencies from your system-wide Python installation.

    ```
    python3 -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**

    ```
    pip install Flask
    ```

4.  **Configure `app.py`:**
    Open `app.py` in your favorite text editor. Locate the line:

    ```
    PASSWORD_STORE_DIR = os.path.expanduser("~/.local/share/password-store")
    ```

    **Change this path** to the absolute path where your GPG password store is located on the server where you're running this application.
    For example, if your password store is at `/home/myuser/passwords`, change it to:

    ```
    PASSWORD_STORE_DIR = "/home/myuser/passwords"
    ```

    If the default `~/.local/share/password-store` is correct for your setup, you can leave it as is.

## Usage

1.  **Run the Flask Application:**
    Make sure your virtual environment is activated (if you created one).
    Navigate to your `password_web_interface` directory in your terminal and run:

    ```
    python app.py
    ```

    The console output will tell you the address where the server is running (e.g., `http://127.0.0.1:5000` or `http://0.0.0.0:5000`).

2.  **Access in Your Browser:**
    Open your web browser and navigate to the address provided by the Flask application (e.g., `http://localhost:5000`).

3.  **Browse and Search:**

    * You will see a tree-like display of your password store.

    * Use the search bar at the top to filter entries by name.

4.  **Decrypt Passwords:**

    * Click the "Show" button next to any password entry.

    * A modal window will appear prompting you for your GPG passphrase.

    * Enter your passphrase and click "Show Password."

    * The decrypted content will appear in the modal.

    * You can then click "Copy to Clipboard" to quickly copy the password.

    * Click the "x" button or outside the modal to close it.

## Contributing

Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please feel free to contribute.

## License

This project is licensed under the [**GNU General Public License v3.0 (GPLv3)**](https://www.gnu.org/licenses/gpl-3.0.html).

