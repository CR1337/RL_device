from flask import Flask
from flask_cors import CORS

from .webapp.routes import api_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(api_bp)
