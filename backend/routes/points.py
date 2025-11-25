from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.utils.helpers import points_to_usd, get_tier_level
from flask_jwt_extended import jwt_required, get_jwt_identity

points_bp = Blueprint('points', __name__)

@points_bp.route('/balance', methods=['GET'])
@jwt_required()
def get_points_balance():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify({
            'points_balance': user.points_balance,
            'total_points_earned': user.total_points_earned,
            'total_points_withdrawn': user.total_points_withdrawn,
            'tier_level': get_tier_level(user.points_balance)
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch points balance', 'error': str(e)}), 500

@points_bp.route('/history', methods=['GET'])
@jwt_required()
def get_points_history():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        transactions = Transaction.query.filter_by(
            user_id=current_user_id,
            type=TransactionType.POINT_WITHDRAWAL
        ).order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'transactions': [t.to_dict() for t in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch points history', 'error': str(e)}), 500

@points_bp.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw_points():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404

        data = request.get_json()
        points = data.get('points', 0)

        if points <= 0:
            return jsonify({'message': 'Points must be greater than 0'}), 400

        if points > user.points_balance:
            return jsonify({'message': 'Insufficient points balance'}), 400

        # Check if user has required bank details
        if not user.bank_name or not user.account_name or not user.account_number:
            return jsonify({'message': 'Please complete your bank details in profile settings before withdrawing'}), 400

        # Check withdrawal tier eligibility
        tier = get_tier_level(user.points_balance)
        if tier == "None":
            return jsonify({'message': 'You must reach Bronze tier (50 points) before withdrawing'}), 400

        # Convert points to USD
        usd_amount = points_to_usd(points)

        # Create pending withdrawal transaction
        transaction = Transaction(
            user_id=current_user_id,
            type=TransactionType.POINT_WITHDRAWAL,
            status=TransactionStatus.PENDING,
            description=f"Withdrawal request: {points} points (${usd_amount:.2f})",
            amount=-usd_amount,
            points_amount=-points
        )

        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            'message': 'Withdrawal request submitted successfully. Payment will be processed within 24-48 hours.',
            'points_requested': points,
            'usd_amount': usd_amount,
            'tier': tier,
            'transaction_id': transaction.id
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to process withdrawal', 'error': str(e)}), 500

@points_bp.route('/convert', methods=['POST'])
@jwt_required()
def convert_points():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404

        data = request.get_json()
        points = data.get('points', 0)

        if points <= 0:
            return jsonify({'message': 'Points must be greater than 0'}), 400

        if points > user.points_balance:
            return jsonify({'message': 'Insufficient points balance'}), 400

        # Convert points to USD (for preview purposes)
        usd_amount = points_to_usd(points)

        return jsonify({
            'message': f'Preview: {points} points = ${usd_amount:.2f}',
            'points': points,
            'usd_amount': usd_amount,
            'current_balance': user.points_balance
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to convert points', 'error': str(e)}), 500
