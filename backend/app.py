from flask import Flask, send_from_directory, request, jsonify
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
    # Get the absolute path to the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define paths to frontend and assets directories
    frontend_folder = os.path.join(project_root, 'frontend')
    static_folder = os.path.join(project_root, 'assets')
    
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///myfigpoint.db'
    
    # Handle different deployment environments
    if os.environ.get('VERCEL') == '1':
        # Use /tmp directory for database in Vercel if not already specified
        if not os.environ.get('DATABASE_URL'):
            database_url = 'sqlite:////tmp/myfigpoint.db'
    elif os.environ.get('RENDER') == 'true':
        # Render provides a PORT environment variable
        pass  # Database URL should come from environment
    
    app = Flask(__name__, static_folder=static_folder)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string-change-in-production'
    
    # Handle Render deployment
    if os.environ.get('RENDER') == 'true':
        # Trust the proxy for HTTPS
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        # Don't set SERVER_NAME as it can cause issues with dynamic hosts
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Serve static files
    @app.route('/')
    def index():
        # Serve the main index.html from the frontend directory
        return send_from_directory(frontend_folder, 'index.html')
    
    # Health check endpoint for Render
    @app.route('/healthz')
    def healthz():
        return {'status': 'ok', 'message': 'MyFigPoint is running on Render!'}
    
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'MyFigPoint is running!'}
    
    # Serve admin files
    @app.route('/admin/')
    def admin_index():
        return send_from_directory(project_root, 'admin/index.html')
    
    @app.route('/admin/<path:filename>')
    def serve_admin_files(filename):
        admin_path = os.path.join(project_root, 'admin', filename)
        # If the file exists in the admin directory, serve it
        if os.path.exists(admin_path) and os.path.isfile(admin_path):
            return send_from_directory(os.path.join(project_root, 'admin'), filename)
        # If not found, serve the admin index.html (for SPA-like behavior)
        return send_from_directory(project_root, 'admin/index.html')
    
    # Serve frontend files
    @app.route('/frontend/')
    def frontend_index():
        return send_from_directory(project_root, 'frontend/index.html')
    
    @app.route('/frontend/<path:filename>')
    def serve_frontend_files(filename):
        frontend_path = os.path.join(project_root, 'frontend', filename)
        # If the file exists in the frontend directory, serve it
        if os.path.exists(frontend_path) and os.path.isfile(frontend_path):
            return send_from_directory(os.path.join(project_root, 'frontend'), filename)
        # If not found, serve the frontend index.html (for SPA-like behavior)
        return send_from_directory(project_root, 'frontend/index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        # Handle Vercel deployment differently for static files
        if os.environ.get('VERCEL') == '1':
            if filename.endswith('.html') or filename.endswith('.css') or filename.endswith('.js'):
                return send_from_directory(frontend_folder, filename)
            return send_from_directory(static_folder, filename)
        else:
            if filename.endswith('.html') or filename.endswith('.css') or filename.endswith('.js'):
                return send_from_directory(frontend_folder, filename)
            return send_from_directory(static_folder, filename)
    
    # Serve the main index.html for all non-API routes (for SPA)
    @app.errorhandler(404)
    def not_found(e):
        # If the request is for an API route, return JSON error
        if request.path.startswith('/api/'):
            return jsonify({'message': 'Endpoint not found'}), 404
        # Otherwise, serve the main index.html (for SPA routing)
        return send_from_directory(frontend_folder, 'index.html')
    
    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.users import users_bp
    from backend.routes.points import points_bp
    from backend.routes.codes import codes_bp
    from backend.routes.transactions import transactions_bp
    from backend.routes.referrals import referrals_bp
    from backend.routes.admin import admin_bp
    from backend.routes.notifications import notifications_bp
    from backend.routes.support import support_bp
    from backend.routes.partners import partners_bp
    from backend.routes.tasks import tasks_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(points_bp, url_prefix='/api/points')
    app.register_blueprint(codes_bp, url_prefix='/api/codes')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(referrals_bp, url_prefix='/api/referrals')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(support_bp, url_prefix='/api/support')
    app.register_blueprint(partners_bp, url_prefix='/api/partners')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app