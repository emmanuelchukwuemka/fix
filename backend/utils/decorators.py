from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.models.user import User, UserRole

def partner_restricted(f):
    """
    Decorator to restrict access for partner accounts from certain routes
    Partners should not be able to redeem codes, do daily tasks, or participate in regular user activities
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        # Check if user is a partner
        if user.role == UserRole.PARTNER:
            return jsonify({
                'message': 'Partners are not allowed to perform this action. '
                          'Please contact admin for assistance.'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function