from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User
from backend.models.reward_code import RewardCode
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.utils.helpers import generate_reward_code
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

codes_bp = Blueprint('codes', __name__)

@codes_bp.route('/redeem', methods=['POST'])
@jwt_required()
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