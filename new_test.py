from waitress import serve
from new_app import app  # assuming 'app' is your Flask app

serve(app, host='0.0.0.0', port=5000)
