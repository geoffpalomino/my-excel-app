FLASK_APP=app.py
FLASK_ENV=development # Enables debug mode and other development features
# FLASK_DEBUG=1 # Alternative way to enable debug mode

# --- Security ---
APP_PASSWORD=yourSuperSecretPassword123 # CHANGE THIS FOR ANY REAL USE!

# --- CORS ---
# LOCAL_FRONTEND_URL=http://localhost:5173 # Default in app.py, can override here
# FRONTEND_URL= # Leave blank for local, set in Azure for production

# --- Logging ---
# No specific log settings here, app.py handles basic logging setup.