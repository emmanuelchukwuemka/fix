from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.models.user import User, UserRole

def require_partner_approval(f):
    """
    Decorator to check if partner accounts are approved before allowing access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        # Check if user is a partner
        if user.role == UserRole.PARTNER:
            # Check if partner is approved
            if not user.is_approved:
                return jsonify({
                    'message': 'Partner account pending approval. Please contact admin.'
                }), 403
                
        return f(*args, **kwargs)
    return decorated_function