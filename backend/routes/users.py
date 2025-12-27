from flask import Blueprint, request, jsonify
from backend.extensions import db, bcrypt
from backend.models.user import User, UserRole
from backend.utils.decorators import partner_restricted
from flask_jwt_extended import jwt_required, get_jwt_identity

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = int(get_jwt_identity())
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
        current_user_id = int(get_jwt_identity())
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
            
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']
            
        if 'country' in data:
            user.country = data['country']
            
        if 'province' in data:
            user.province = data['province']
            
        if 'routing_number' in data:
            user.routing_number = data['routing_number']
            
        if 'swift_code' in data:
            user.swift_code = data['swift_code']
            
        if 'account_type' in data:
            user.account_type = data['account_type']
            
        if 'bank_address' in data:
            user.bank_address = data['bank_address']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update profile', 'error': str(e)}), 500

@users_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'message': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not bcrypt.check_password_hash(user.password_hash, current_password):
            return jsonify({'message': 'Current password is incorrect'}), 400
        
        # Validate new password
        if len(new_password) < 6:
            return jsonify({'message': 'New password must be at least 6 characters long'}), 400
        
        # Hash and update new password
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to change password', 'error': str(e)}), 500

@users_bp.route('/admin/<int:user_id>/role', methods=['PUT'])
@jwt_required()
def update_user_role(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        new_role = data.get('role')
        
        if not new_role:
            return jsonify({'message': 'Role is required'}), 400
        
        # Validate role
        try:
            user.role = UserRole(new_role)
        except ValueError:
            return jsonify({'message': 'Invalid role value'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'User role updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update user role', 'error': str(e)}), 500

@users_bp.route('/admin/<int:user_id>/points', methods=['PUT'])
@jwt_required()
def admin_update_user_points(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        points = data.get('points', 0)
        operation = data.get('operation', 'set')  # set, add, subtract
        
        if operation == 'set':
            user.points_balance = points
        elif operation == 'add':
            user.points_balance += points
            user.total_points_earned += points
        elif operation == 'subtract':
            if user.points_balance < points:
                return jsonify({'message': 'Insufficient points balance'}), 400
            user.points_balance -= points
            user.total_points_withdrawn += points
        else:
            return jsonify({'message': 'Invalid operation. Use "set", "add", or "subtract"'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'User points {operation} successfully',
            'user_id': user_id,
            'new_balance': user.points_balance
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update user points', 'error': str(e)}), 500

@users_bp.route('/admin/search', methods=['GET'])
@jwt_required()
def search_users():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        query = request.args.get('query', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({'message': 'Search query is required'}), 400
        
        users = User.query.filter(
            db.or_(
                User.full_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.referral_code.ilike(f'%{query}%')
            )
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to search users', 'error': str(e)}), 500


@users_bp.route('/avatar', methods=['POST'])
@jwt_required()
@partner_restricted
def upload_avatar():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if 'avatar' not in request.files:
            return jsonify({'message': 'No avatar file provided'}), 400
        
        file = request.files['avatar']
        
        if file.filename == '':
            return jsonify({'message': 'No avatar file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' not in file.filename or \
           file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'message': 'Invalid file type. Allowed types: png, jpg, jpeg, gif, webp'}), 400
        
        # In a real application, you would save the file to storage (local/cloud)
        # For now, we'll store the avatar as a data URL in the database
        import base64
        file_data = file.read()
        encoded_string = base64.b64encode(file_data).decode('utf-8')
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        avatar_url = f'data:image/{file_extension};base64,{encoded_string}'
        
        user.avatar_url = avatar_url
        db.session.commit()
        
        return jsonify({
            'message': 'Avatar uploaded successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to upload avatar', 'error': str(e)}), 500