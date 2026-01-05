from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os

# Import the admin auth decorator
from backend.utils.admin_auth import admin_required

# Import extensions
from backend.extensions import db, bcrypt, jwt

def create_app():
    # Get the absolute path to the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define paths to frontend and assets directories
    frontend_folder = os.path.join(project_root, 'frontend')
    static_folder = os.path.join(project_root, 'assets')
    
    # Use absolute path for database in instance folder
    instance_path = os.path.join(project_root, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    db_path = os.path.join(instance_path, 'myfigpoint.db')
    database_url = os.environ.get('DATABASE_URL') or f'sqlite:///{db_path}'
    
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
    from datetime import timedelta
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
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
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token has expired', 'error': 'token_expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Invalid token', 'error': 'invalid_token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Authorization token is required', 'error': 'authorization_required'}), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token has been revoked', 'error': 'token_revoked'}), 401
    
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
        # Serve the admin login page by default
        return send_from_directory(project_root, 'admin/login.html')
    
    @app.route('/admin/dashboard')
    def admin_dashboard():
        # Serve the actual admin dashboard
        return send_from_directory(project_root, 'admin/index.html')
    
    @app.route('/admin/tasks')
    def admin_tasks():
        # Serve the admin tasks page
        return send_from_directory(project_root, 'admin/tasks.html')
    
    @app.route('/admin/referrals')
    def admin_referrals():
        # Serve the admin referrals page
        return send_from_directory(project_root, 'admin/referrals.html')
    
    @app.route('/admin/withdrawals')
    def admin_withdrawals():
        # Serve the admin withdrawals page
        return send_from_directory(project_root, 'admin/withdrawals.html')
    
    @app.route('/admin/activities')
    def admin_activities():
        # Serve the admin activities page
        return send_from_directory(project_root, 'admin/activities.html')
    
    @app.route('/admin/codes')
    def admin_codes():
        # Serve the admin codes page
        return send_from_directory(project_root, 'admin/codes.html')
    
    @app.route('/admin/support')
    def admin_support():
        # Serve the admin support page
        return send_from_directory(project_root, 'admin/support.html')
    
    @app.route('/admin/profiles')
    def admin_profiles():
        # Serve the admin profiles page
        return send_from_directory(project_root, 'admin/profiles.html')
    
    @app.route('/admin/users')
    def admin_users():
        # Serve the admin users page
        return send_from_directory(project_root, 'admin/users.html')
    
    @app.route('/admin/partners')
    def admin_partners():
        # Serve the admin partners page
        return send_from_directory(project_root, 'admin/partners.html')
    
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
    
    # Serve manifest.json with correct MIME type
    @app.route('/manifest.json')
    def serve_manifest():
        return send_from_directory(frontend_folder, 'manifest.json', mimetype='application/manifest+json')
    
    # Serve service-worker.js with correct MIME type
    @app.route('/service-worker.js')
    def serve_service_worker():
        return send_from_directory(frontend_folder, 'service-worker.js', mimetype='application/javascript')
    
    # Serve uploaded files
    @app.route('/uploads/task_proofs/<filename>')
    def serve_uploaded_task_proof(filename):
        upload_dir = os.path.join(project_root, 'uploads', 'task_proofs')
        return send_from_directory(upload_dir, filename)
    
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
    
    # Main API endpoint
    @app.route('/api')
    def api_info():
        return jsonify({
            'message': 'MyFigPoint API',
            'version': '1.0.0',
            'description': 'This is the main API endpoint for MyFigPoint application',
            'endpoints': {
                '/api/auth': 'Authentication endpoints',
                '/api/users': 'User management endpoints',
                '/api/points': 'Points management endpoints',
                '/api/codes': 'Redeem code endpoints',
                '/api/transactions': 'Transaction endpoints',
                '/api/referrals': 'Referral system endpoints',
                '/api/admin': 'Admin endpoints',
                '/api/notifications': 'Notification endpoints',
                '/api/support': 'Support system endpoints',
                '/api/partners': 'Partner management endpoints',
                '/api/tasks': 'Task management endpoints'
            },
            'documentation': '/api/docs'  # Placeholder for future documentation
        }), 200
    
    # API Documentation endpoint
    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            'api_documentation': {
                'title': 'MyFigPoint API Documentation',
                'version': '1.0.0',
                'description': 'This API provides access to MyFigPoint services including user management, points system, referrals, tasks, and more.',
                'base_url': request.url_root,
                'available_endpoints': [
                    {
                        'endpoint': '/api/auth',
                        'methods': ['POST', 'GET'],
                        'description': 'Handles user authentication including login, signup, and token management'
                    },
                    {
                        'endpoint': '/api/users',
                        'methods': ['GET', 'PUT'],
                        'description': 'Manages user profiles, including profile updates and user search (admin only)'
                    },
                    {
                        'endpoint': '/api/points',
                        'methods': ['GET', 'POST'],
                        'description': 'Handles points management for users'
                    },
                    {
                        'endpoint': '/api/codes',
                        'methods': ['GET', 'POST'],
                        'description': 'Manages redeem codes for points'
                    },
                    {
                        'endpoint': '/api/transactions',
                        'methods': ['GET'],
                        'description': 'Provides transaction history for users'
                    },
                    {
                        'endpoint': '/api/referrals',
                        'methods': ['GET', 'POST'],
                        'description': 'Manages referral system and rewards'
                    },
                    {
                        'endpoint': '/api/admin',
                        'methods': ['GET', 'POST', 'PUT', 'DELETE'],
                        'description': 'Admin-specific endpoints for managing the platform'
                    },
                    {
                        'endpoint': '/api/notifications',
                        'methods': ['GET', 'POST'],
                        'description': 'Handles user notifications'
                    },
                    {
                        'endpoint': '/api/support',
                        'methods': ['GET', 'POST'],
                        'description': 'Support ticket system'
                    },
                    {
                        'endpoint': '/api/partners',
                        'methods': ['GET', 'POST', 'PUT'],
                        'description': 'Partner management and approval system'
                    },
                    {
                        'endpoint': '/api/tasks',
                        'methods': ['GET', 'POST', 'PUT'],
                        'description': 'Task management for users to earn points'
                    }
                ]
            }
        }), 200
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app