from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.models.reward_code import RewardCode
from backend.utils.helpers import generate_batch_id, generate_reward_code
from backend.utils.partner_approval import require_partner_approval
from flask_jwt_extended import jwt_required, get_jwt_identity

partners_bp = Blueprint('partners', __name__)

@partners_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_partner_stats():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        # Check if user is a partner
        if user.role != UserRole.PARTNER:
            return jsonify({'message': 'Access denied. Partner access required.'}), 403
        
        # Check if partner is approved
        if not user.is_approved:
            return jsonify({'message': 'Partner account pending approval. Please contact admin.'}), 403
        
        # Get partner statistics
        # Count referred users
        referred_count = User.query.filter_by(referred_by=current_user_id).count()
        
        # Calculate total earnings from referrals
        referral_earnings = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.REFERRAL_BONUS,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        # Calculate total points earned
        referral_points = db.session.query(db.func.sum(Transaction.points_amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.REFERRAL_BONUS,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        return jsonify({
            'referred_users_count': referred_count,
            'total_earnings': abs(referral_earnings),
            'total_points_earned': abs(referral_points),
            'partner_since': user.created_at.isoformat() if user.created_at else None
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch partner stats', 'error': str(e)}), 500

@partners_bp.route('/referrals', methods=['GET'])
@jwt_required()
def get_partner_referrals():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        # Check if user is a partner
        if user.role != UserRole.PARTNER:
            return jsonify({'message': 'Access denied. Partner access required.'}), 403
        
        # Check if partner is approved
        if not user.is_approved:
            return jsonify({'message': 'Partner account pending approval. Please contact admin.'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        referred_users = User.query.filter_by(referred_by=current_user_id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'referrals': [user.to_dict() for user in referred_users.items],
            'total': referred_users.total,
            'pages': referred_users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch partner referrals', 'error': str(e)}), 500

@partners_bp.route('/commission-rates', methods=['GET'])
@jwt_required()
def get_commission_rates():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        # Check if user is a partner
        if user.role != UserRole.PARTNER:
            return jsonify({'message': 'Access denied. Partner access required.'}), 403
        
        # Check if partner is approved
        if not user.is_approved:
            return jsonify({'message': 'Partner account pending approval. Please contact admin.'}), 403
        
        # Commission rates based on tier
        commission_rates = {
            'bronze': {
                'referral_bonus': 5.0,  # percentage
                'monthly_payout': 'Net 30'
            },
            'silver': {
                'referral_bonus': 7.5,
                'monthly_payout': 'Net 15'
            },
            'gold': {
                'referral_bonus': 10.0,
                'monthly_payout': 'Net 7'
            },
            'platinum': {
                'referral_bonus': 15.0,
                'monthly_payout': 'Net 7'
            }
        }
        
        # Determine partner tier based on referred users count
        referred_count = User.query.filter_by(referred_by=current_user_id).count()
        if referred_count >= 1000:
            tier = 'platinum'
        elif referred_count >= 500:
            tier = 'gold'
        elif referred_count >= 100:
            tier = 'silver'
        else:
            tier = 'bronze'
        
        return jsonify({
            'current_tier': tier,
            'referred_users_count': referred_count,
            'commission_rate': commission_rates[tier]['referral_bonus'],
            'payout_terms': commission_rates[tier]['monthly_payout'],
            'next_tier_requirements': {
                'silver': 100,
                'gold': 500,
                'platinum': 1000
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch commission rates', 'error': str(e)}), 500

@partners_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_partner_dashboard():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        # Check if user is a partner
        if user.role != UserRole.PARTNER:
            return jsonify({'message': 'Access denied. Partner access required.'}), 403
        
        # Check if partner is approved
        if not user.is_approved:
            return jsonify({'message': 'Partner account pending approval. Please contact admin.'}), 403
        
        # Get partner statistics
        # Count referred users
        referred_count = User.query.filter_by(referred_by=current_user_id).count()
        
        # Calculate total earnings from referrals
        referral_earnings = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.REFERRAL_BONUS,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        # Calculate total points earned
        referral_points = db.session.query(db.func.sum(Transaction.points_amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.REFERRAL_BONUS,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        return jsonify({
            'referred_users_count': referred_count,
            'total_earnings': abs(referral_earnings),
            'total_points_earned': abs(referral_points),
            'partner_since': user.created_at.isoformat() if user.created_at else None
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch partner dashboard', 'error': str(e)}), 500

@partners_bp.route('/admin/promote', methods=['POST'])
@jwt_required()
def promote_to_partner():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'message': 'User ID is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Promote user to partner but require approval
        user.role = UserRole.PARTNER
        user.is_approved = False  # Partners need admin approval
        
        db.session.commit()
        
        return jsonify({
            'message': f'User {user.full_name} promoted to partner successfully. Awaiting admin approval.',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to promote user to partner', 'error': str(e)}), 500

@partners_bp.route('/admin/demote', methods=['POST'])
@jwt_required()
def demote_from_partner():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'message': 'User ID is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Demote partner to user
        user.role = UserRole.USER
        
        db.session.commit()
        
        return jsonify({
            'message': f'Partner {user.full_name} demoted to user successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to demote partner to user', 'error': str(e)}), 500

@partners_bp.route('/admin/approve', methods=['POST'])
@jwt_required()
def approve_partner():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'message': 'User ID is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Check if user is a partner
        if user.role != UserRole.PARTNER:
            return jsonify({'message': 'User is not a partner'}), 400
        
        # Approve partner
        user.is_approved = True
        
        db.session.commit()
        
        return jsonify({
            'message': f'Partner {user.full_name} approved successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to approve partner', 'error': str(e)}), 500

@partners_bp.route('/admin/deny', methods=['POST'])
@jwt_required()
def deny_partner():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'message': 'User ID is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Check if user is a partner
        if user.role != UserRole.PARTNER:
            return jsonify({'message': 'User is not a partner'}), 400
        
        # Deny partner (demote back to user)
        user.role = UserRole.USER
        user.is_approved = False
        
        db.session.commit()
        
        return jsonify({
            'message': f'Partner {user.full_name} denied and demoted to user successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to deny partner', 'error': str(e)}), 500

@partners_bp.route('/admin/list', methods=['GET'])
@jwt_required()
def list_partners():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query.filter_by(role=UserRole.PARTNER)
        
        if search:
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        partners = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Add approval status to partner data
        partners_data = []
        for partner in partners.items:
            partner_data = partner.to_dict()
            partner_data['approval_status'] = 'approved' if partner.is_approved else 'pending'
            partners_data.append(partner_data)
        
        return jsonify({
            'partners': partners_data,
            'total': partners.total,
            'pages': partners.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to list partners', 'error': str(e)}), 500

@partners_bp.route('/codes/generate', methods=['POST'])
@jwt_required()
def generate_partner_codes():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        # Check if user is partner
        if user.role != UserRole.PARTNER and user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        # Check if partner is approved
        if user.role == UserRole.PARTNER and not user.is_approved:
            return jsonify({'message': 'Partner account pending approval. Please contact admin.'}), 403
        
        data = request.get_json()
        count = data.get('count', 100)
        point_value = data.get('point_value', 0.1)
        partner_id = data.get('partner_id', current_user_id)
        
        # Partners can only generate codes for themselves unless they're admin
        if user.role == UserRole.PARTNER and partner_id != current_user_id:
            return jsonify({'message': 'Partners can only generate codes for themselves'}), 403
        
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