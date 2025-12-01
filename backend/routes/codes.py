from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.reward_code import RewardCode
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.utils.helpers import generate_reward_code
from backend.utils.decorators import partner_restricted
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import re

codes_bp = Blueprint('codes', __name__)

@codes_bp.route('/redeem', methods=['POST'])
@jwt_required()
@partner_restricted
def redeem_code():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        code_value = data.get('code', '').upper()
        
        if not code_value:
            return jsonify({'message': 'Code is required'}), 400
        
        # Validate code format: 5 uppercase letters + 3 digits
        if not re.match(r'^[A-Z]{5}[0-9]{3}$', code_value):
            return jsonify({'message': 'Invalid code format. Code must be 5 uppercase letters followed by 3 digits (e.g., ABCDE123)'}), 400
        
        # Find the code
        reward_code = RewardCode.query.filter_by(code=code_value).first()
        
        if not reward_code:
            return jsonify({'message': 'Invalid code'}), 404
        
        if reward_code.is_used:
            return jsonify({'message': 'Code has already been used'}), 400
        
        # Mark code as used
        reward_code.is_used = True
        reward_code.used_by = current_user_id
        reward_code.used_at = datetime.utcnow()
        
        # Add points to user
        user.points_balance += reward_code.point_value
        user.total_points_earned += reward_code.point_value
        
        # Create transaction record
        transaction = Transaction(
            user_id=current_user_id,
            type=TransactionType.CODE_REDEMPTION,
            status=TransactionStatus.COMPLETED,
            description=f"Redeemed code {code_value}",
            amount=0,
            points_amount=reward_code.point_value,
            reference_id=reward_code.id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully redeemed code for {reward_code.point_value} points',
            'points_added': reward_code.point_value,
            'new_balance': user.points_balance
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to redeem code', 'error': str(e)}), 500

@codes_bp.route('/history', methods=['GET'])
@jwt_required()
@partner_restricted
def get_redemption_history():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        codes = RewardCode.query.filter_by(used_by=current_user_id).order_by(
            RewardCode.used_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'codes': [code.to_dict() for code in codes.items],
            'total': codes.total,
            'pages': codes.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch redemption history', 'error': str(e)}), 500

@codes_bp.route('/validate/<code>', methods=['GET'])
@jwt_required()
def validate_code(code):
    try:
        reward_code = RewardCode.query.filter_by(code=code.upper()).first()
        
        if not reward_code:
            return jsonify({'valid': False, 'message': 'Invalid code'}), 404
        
        if reward_code.is_used:
            return jsonify({'valid': False, 'message': 'Code has already been used'}), 400
        
        return jsonify({
            'valid': True,
            'code': reward_code.code,
            'point_value': reward_code.point_value,
            'created_at': reward_code.created_at
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to validate code', 'error': str(e)}), 500

@codes_bp.route('/info/<code>', methods=['GET'])
@jwt_required()
def get_code_info(code):
    try:
        reward_code = RewardCode.query.filter_by(code=code.upper()).first()
        
        if not reward_code:
            return jsonify({'valid': False, 'message': 'Invalid code'}), 404
        
        if reward_code.is_used:
            return jsonify({'valid': False, 'message': 'Code has already been used'}), 400
        
        return jsonify({
            'valid': True,
            'code': reward_code.code,
            'point_value': reward_code.point_value,
            'created_at': reward_code.created_at,
            'is_used': reward_code.is_used,
            'used_by': reward_code.used_by,
            'used_at': reward_code.used_at
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to get code info', 'error': str(e)}), 500

@codes_bp.route('/admin/all', methods=['GET'])
@jwt_required()
def get_all_codes():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        used_only = request.args.get('used_only', 'false').lower() == 'true'
        batch_id = request.args.get('batch_id', '')
        
        query = RewardCode.query
        
        if used_only:
            query = query.filter_by(is_used=True)
            
        if batch_id:
            query = query.filter_by(batch_id=batch_id)
        
        codes = query.order_by(RewardCode.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'codes': [code.to_dict() for code in codes.items],
            'total': codes.total,
            'pages': codes.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch codes', 'error': str(e)}), 500

@codes_bp.route('/admin/<int:code_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_code(code_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        code = RewardCode.query.get(code_id)
        if not code:
            return jsonify({'message': 'Code not found'}), 404
        
        # Don't allow deletion of used codes
        if code.is_used:
            return jsonify({'message': 'Cannot delete used codes'}), 400
        
        db.session.delete(code)
        db.session.commit()
        
        return jsonify({'message': 'Code deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to delete code', 'error': str(e)}), 500

@codes_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_code_stats():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        total_codes = RewardCode.query.count()
        used_codes = RewardCode.query.filter_by(is_used=True).count()
        unused_codes = total_codes - used_codes
        
        # Get stats by batch
        batch_stats = db.session.query(
            RewardCode.batch_id,
            db.func.count(RewardCode.id).label('total'),
            db.func.sum(db.case((RewardCode.is_used == True, 1), else_=0)).label('used')
        ).group_by(RewardCode.batch_id).all()
        
        batch_data = []
        for batch in batch_stats:
            batch_data.append({
                'batch_id': batch.batch_id,
                'total': batch.total,
                'used': batch.used,
                'unused': batch.total - batch.used
            })
        
        return jsonify({
            'total_codes': total_codes,
            'used_codes': used_codes,
            'unused_codes': unused_codes,
            'batch_stats': batch_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch code stats', 'error': str(e)}), 500
