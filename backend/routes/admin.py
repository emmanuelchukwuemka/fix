from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.reward_code import RewardCode
from backend.utils.helpers import generate_reward_code, generate_batch_id
from flask_jwt_extended import jwt_required, get_jwt_identity
import csv
import io

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/codes/generate', methods=['POST'])
@jwt_required()
def generate_codes():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        count = data.get('count', 100)
        point_value = data.get('point_value', 0.1)
        
        if count <= 0 or count > 10000:
            return jsonify({'message': 'Count must be between 1 and 10,000'}), 400
        
        if point_value <= 0:
            return jsonify({'message': 'Point value must be greater than 0'}), 400
        
        # Generate batch ID
        batch_id = generate_batch_id()
        
        # Generate codes
        codes = []
        for _ in range(count):
            code = generate_reward_code()
            reward_code = RewardCode(
                code=code,
                point_value=point_value,
                batch_id=batch_id
            )
            db.session.add(reward_code)
            codes.append(code)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully generated {count} codes',
            'batch_id': batch_id,
            'codes': codes[:10],  # Return first 10 codes as sample
            'total_generated': count
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Failed to generate codes', 'error': str(e)}), 500

@admin_bp.route('/codes/export/<batch_id>', methods=['GET'])
@jwt_required()
def export_codes(batch_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get codes for this batch
        codes = RewardCode.query.filter_by(batch_id=batch_id).all()
        
        if not codes:
            return jsonify({'message': 'No codes found for this batch'}), 404
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Code', 'Point Value', 'Batch ID', 'Created At'])
        
        for code in codes:
            writer.writerow([
                code.code,
                code.point_value,
                code.batch_id,
                code.created_at.isoformat()
            ])
        
        csv_data = output.getvalue()
        output.close()
        
        return jsonify({
            'batch_id': batch_id,
            'code_count': len(codes),
            'csv_data': csv_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to export codes', 'error': str(e)}), 500

@admin_bp.route('/codes/used', methods=['GET'])
@jwt_required()
def get_used_codes():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        codes = RewardCode.query.filter_by(is_used=True).order_by(
            RewardCode.used_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'codes': [code.to_dict() for code in codes.items],
            'total': codes.total,
            'pages': codes.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch used codes', 'error': str(e)}), 500

@admin_bp.route('/codes/used/delete', methods=['DELETE'])
@jwt_required()
def delete_used_codes():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        code_ids = data.get('code_ids', [])
        
        if not code_ids:
            return jsonify({'message': 'No code IDs provided'}), 400
        
        # Delete used codes
        deleted_count = RewardCode.query.filter(
            RewardCode.id.in_(code_ids),
            RewardCode.is_used == True
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully deleted {deleted_count} used codes',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to delete used codes', 'error': str(e)}), 500

@admin_bp.route('/users/points/update', methods=['POST'])
@jwt_required()
def update_user_points():
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        points = data.get('points', 0)
        operation = data.get('operation', 'add')  # add or subtract
        
        if not user_id:
            return jsonify({'message': 'User ID is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Update points based on operation
        if operation == 'add':
            user.points_balance += points
            user.total_points_earned += points
        elif operation == 'subtract':
            if user.points_balance < points:
                return jsonify({'message': 'Insufficient points balance'}), 400
            user.points_balance -= points
            user.total_points_withdrawn += points
        else:
            return jsonify({'message': 'Invalid operation. Use "add" or "subtract"'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully {"added" if operation == "add" else "subtracted"} {points} points',
            'user_id': user_id,
            'new_balance': user.points_balance
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update user points', 'error': str(e)}), 500