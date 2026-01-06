from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.user import User, UserRole


def admin_required(f):
    """
    Decorator to require admin authentication for routes
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            # Get the user ID from the JWT token
            user_id = get_jwt_identity()
            
            # Get the user
            user = User.query.get(user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            # Check if user is suspended
            if user.is_suspended:
                return jsonify({'message': 'Your account has been suspended. Please contact support for assistance.'}), 403
            
            # Check if user is admin
            if user.role != UserRole.ADMIN:
                return jsonify({'message': 'Admin access required'}), 403
                
            # If everything is fine, proceed with the route
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Authentication failed', 'error': str(e)}), 401
    
    return decorated_function