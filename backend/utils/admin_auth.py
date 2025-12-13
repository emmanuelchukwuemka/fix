from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import decode_token, get_jwt_identity
from backend.models.user import User, UserRole
import os

def admin_required(f):
    """
    Decorator to require admin authentication for routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get the token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'message': 'Missing or invalid authorization header'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Decode the token
            decoded_token = decode_token(token)
            user_id = decoded_token['identity']
            
            # Get the user
            user = User.query.get(user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            # Check if user is admin
            if user.role != UserRole.ADMIN:
                return jsonify({'message': 'Admin access required'}), 403
                
            # If everything is fine, proceed with the route
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Authentication failed', 'error': str(e)}), 401
    
    return decorated_function