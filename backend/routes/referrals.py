from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from flask_jwt_extended import jwt_required, get_jwt_identity

referrals_bp = Blueprint('referrals', __name__)

@referrals_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_referral_stats():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Count referred users
        referred_count = User.query.filter_by(referred_by=current_user_id).count()
        
        # Calculate referral earnings
        referral_earnings = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.REFERRAL_BONUS,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        # Calculate referral points
        referral_points = db.session.query(db.func.sum(Transaction.points_amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.REFERRAL_BONUS,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        return jsonify({
            'referral_code': user.referral_code,
            'referred_users_count': referred_count,
            'total_referral_earnings': abs(referral_earnings),
            'total_referral_points': abs(referral_points)
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch referral stats', 'error': str(e)}), 500

@referrals_bp.route('/users', methods=['GET'])
@jwt_required()
def get_referred_users():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        referred_users = User.query.filter_by(referred_by=current_user_id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in referred_users.items],
            'total': referred_users.total,
            'pages': referred_users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch referred users', 'error': str(e)}), 500

@referrals_bp.route('/link', methods=['GET'])
@jwt_required()
def get_referral_link():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        referral_link = f"https://myfigpoint.com/register?ref={user.referral_code}"
        
        return jsonify({
            'referral_code': user.referral_code,
            'referral_link': referral_link
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to generate referral link', 'error': str(e)}), 500