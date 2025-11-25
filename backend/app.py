from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, static_folder='../assets')
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///myfigpoint.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string-change-in-production'
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Serve static files
    @app.route('/')
    def index():
        return send_from_directory('../', 'index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        if filename.endswith('.html') or filename.endswith('.css') or filename.endswith('.js'):
            return send_from_directory('../', filename)
        return send_from_directory('../assets', filename)
    
    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.users import users_bp
    from backend.routes.points import points_bp
    from backend.routes.codes import codes_bp
    from backend.routes.transactions import transactions_bp
    from backend.routes.referrals import referrals_bp
    from backend.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(points_bp, url_prefix='/api/points')
    app.register_blueprint(codes_bp, url_prefix='/api/codes')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(referrals_bp, url_prefix='/api/referrals')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app