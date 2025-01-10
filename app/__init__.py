from flask import Flask
from flask_cors import CORS
from config import Config
import os
from dotenv import load_dotenv

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    load_dotenv()

    # Dynamically set CORS origins based on environment
    if os.getenv('FLASK_ENV') == 'development':
        CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:5000", "http://localhost:5173"]}})
    else:
        CORS(app, resources={r"/*": {"origins": "https://resume-intelli.vercel.app"}})

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    from app.routes import api
    app.register_blueprint(api)

    return app
