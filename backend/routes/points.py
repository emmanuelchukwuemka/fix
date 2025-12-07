from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.utils.helpers import points_to_usd, get_tier_level
from backend.utils.emailer import Emailer
from backend.utils.decorators import partner_restricted
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
@partner_restricted
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
@partner_restricted
def withdraw_points():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request data'}), 400
            
        points = data.get('points', 0)
        method = data.get('method', 'bank')  # Default to bank transfer

        # Validate points amount
        if not isinstance(points, (int, float)):
            return jsonify({'message': 'Points must be a number'}), 400
            
        if points <= 0:
            return jsonify({'message': 'Points must be greater than 0'}), 400

        if points > user.points_balance:
            return jsonify({'message': 'Insufficient points balance'}), 400

        # Validate payment method
        valid_methods = ['bank', 'gift_card']
        if method not in valid_methods:
            return jsonify({'message': f'Invalid payment method. Valid methods: {", ".join(valid_methods)}'}), 400

        # Check if user has required details based on payment method
        if method == 'bank':
            # Update user's banking details if provided in the request
            if data.get('bank_name'):
                user.bank_name = data['bank_name']
            if data.get('account_holder_name'):
                user.account_name = data['account_holder_name']
            if data.get('account_number'):
                user.account_number = data['account_number']
            
            # Validate that user has all required banking details
            if not user.bank_name or not user.account_name or not user.account_number:
                return jsonify({'message': 'Please complete your bank details in profile settings before withdrawing via bank transfer'}), 400
        elif method == 'gift_card' and not data.get('gift_card_type'):
            return jsonify({'message': 'Gift card type is required for gift card withdrawals'}), 400

        # Check withdrawal tier eligibility
        tier = get_tier_level(user.points_balance)
        if tier == "None":
            return jsonify({'message': 'You must reach Bronze tier (50 points) before withdrawing'}), 400

        # Convert points to USD
        usd_amount = points_to_usd(points)
        
        # Store original balance for rollback if needed
        original_balance = user.points_balance
        original_withdrawn_points = user.total_points_withdrawn
        original_withdrawn_amount = user.total_withdrawn

        # Deduct points from user balance
        user.points_balance -= points
        user.total_points_withdrawn += points
        user.total_withdrawn += usd_amount

        # Create pending withdrawal transaction
        description = f"Withdrawal request: {points} points (${usd_amount:.2f}) via {method}"
        if method == 'bank':
            description += f" to {user.bank_name} account ending in {user.account_number[-4:] if user.account_number else '****'}"
        elif method == 'gift_card':
            gift_card_type = data.get('gift_card_type', 'gift card')
            if not gift_card_type or not isinstance(gift_card_type, str):
                # Rollback changes
                user.points_balance = original_balance
                user.total_points_withdrawn = original_withdrawn_points
                user.total_withdrawn = original_withdrawn_amount
                return jsonify({'message': 'Invalid gift card type'}), 400
            description += f" as {gift_card_type}"

        transaction = Transaction(
            user_id=current_user_id,
            type=TransactionType.POINT_WITHDRAWAL,
            status=TransactionStatus.PENDING,
            description=description,
            amount=-usd_amount,
            points_amount=-points,
            reference_id=data.get('gift_card_type')
        )

        db.session.add(transaction)
        db.session.commit()

        # Send email notification
        emailer = Emailer()
        email_sent = emailer.send_withdrawal_request_notification(
            user_email=user.email,
            user_name=user.full_name,
            points=points,
            amount=usd_amount,
            method=method
        )
        
        # Log email sending status (for debugging)
        if not email_sent:
            print(f"Warning: Failed to send withdrawal notification email to {user.email}")

        return jsonify({
            'message': f'Withdrawal request for {points} points (${usd_amount:.2f}) submitted successfully. Payment will be processed within 24-48 hours.',
            'points_requested': points,
            'usd_amount': usd_amount,
            'method': method,
            'tier': tier,
            'transaction_id': transaction.id,
            'new_balance': user.points_balance
        }), 200

    except Exception as e:
        # Log the error for debugging
        print(f"Error processing withdrawal: {str(e)}")
        
        # Attempt to rollback any changes if session is still active
        try:
            db.session.rollback()
        except:
            pass
            
        return jsonify({
            'message': 'Failed to process withdrawal. Please try again later.',
            'error': 'An internal error occurred while processing your request'
        }), 500

@points_bp.route('/convert', methods=['POST'])
@jwt_required()
@partner_restricted
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
