from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.utils.decorators import partner_restricted
from flask_jwt_extended import jwt_required, get_jwt_identity

referrals_bp = Blueprint('referrals', __name__)

@referrals_bp.route('/stats', methods=['GET'])
@jwt_required()
@partner_restricted
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

@referrals_bp.route('/admin/all', methods=['GET'])
@jwt_required()
def get_all_referrals():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query.filter(User.referred_by.isnot(None))
        
        if search:
            query = query.join(User.referrer).filter(
                db.or_(
                    User.full_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%'),
                    User.referral_code.ilike(f'%{search}%'),
                    User.referrer.full_name.ilike(f'%{search}%')
                )
            )
        
        referrals = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        referral_data = []
        for referral in referrals.items:
            referral_data.append({
                'id': referral.id,
                'full_name': referral.full_name,
                'email': referral.email,
                'referral_code': referral.referral_code,
                'referred_by_code': referral.referrer.referral_code if referral.referrer else None,
                'referred_by_name': referral.referrer.full_name if referral.referrer else None,
                'points_balance': referral.points_balance,
                'total_earnings': referral.total_earnings,
                'created_at': referral.created_at
            })
        
        return jsonify({
            'referrals': referral_data,
            'total': referrals.total,
            'pages': referrals.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch referrals', 'error': str(e)}), 500

@referrals_bp.route('/admin/bonuses', methods=['GET'])
@jwt_required()
def get_referral_bonuses():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get referral bonus transactions
        transactions = Transaction.query.filter_by(
            type=TransactionType.REFERRAL_BONUS
        ).order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'bonuses': [transaction.to_dict() for transaction in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch referral bonuses', 'error': str(e)}), 500

@referrals_bp.route('/admin/top-referrers', methods=['GET'])
@jwt_required()
def get_top_referrers():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get users with the most referrals
        top_referrers = db.session.query(
            User,
            db.func.count(User.referred_users).label('referral_count')
        ).join(User.referred_users).group_by(User.id).order_by(
            db.desc('referral_count')
        ).limit(10).all()
        
        referrer_data = []
        for user, count in top_referrers:
            referrer_data.append({
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'referral_code': user.referral_code,
                'referral_count': count,
                'total_earnings': user.total_earnings
            })
        
        return jsonify({'top_referrers': referrer_data}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch top referrers', 'error': str(e)}), 500

@referrals_bp.route('/users', methods=['GET'])
@jwt_required()
@partner_restricted
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
@partner_restricted
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