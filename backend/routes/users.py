from flask import Blueprint, request, jsonify
from backend.app import db, bcrypt
from backend.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch profile', 'error': str(e)}), 500

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'bank_name' in data:
            user.bank_name = data['bank_name']
        if 'account_name' in data:
            user.account_name = data['account_name']
        if 'account_number' in data:
            user.account_number = data['account_number']
        if 'password' in data:
            user.password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update profile', 'error': str(e)}), 500

@users_bp.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify({
            'points_balance': user.points_balance,
            'total_earnings': user.total_earnings,
            'total_withdrawn': user.total_withdrawn
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch balance', 'error': str(e)}), 500