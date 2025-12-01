from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.reward_code import RewardCode
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.utils.helpers import generate_reward_code, generate_batch_id
from backend.utils.emailer import Emailer
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

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch users', 'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/details', methods=['GET'])
@jwt_required()
def get_user_details(user_id):
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch user details', 'error': str(e)}), 500

@admin_bp.route('/support-messages', methods=['GET'])
@jwt_required()
def get_all_support_messages():
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        
        query = SupportMessage.query
        
        if status:
            query = query.filter_by(status=MessageStatus(status))
        
        messages = query.order_by(SupportMessage.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'messages': [msg.to_dict() for msg in messages.items],
            'total': messages.total,
            'pages': messages.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch support messages', 'error': str(e)}), 500

@admin_bp.route('/support-messages/<int:message_id>/respond', methods=['POST'])
@jwt_required()
def respond_to_support_message(message_id):
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        message = SupportMessage.query.get(message_id)
        if not message:
            return jsonify({'message': 'Support message not found'}), 404
        
        data = request.get_json()
        response_text = data.get('response', '').strip()
        
        if not response_text:
            return jsonify({'message': 'Response text is required'}), 400
        
        # Create response message
        response_msg = SupportMessage(
            user_id=message.user_id,
            subject=f"Re: {message.subject}",
            message=response_text,
            message_type=MessageType.SUPPORT_TO_USER,
            status=MessageStatus.REPLIED
        )
        
        # Update original message status
        message.response = response_text
        message.status = MessageStatus.REPLIED
        
        db.session.add(response_msg)
        db.session.commit()
        
        return jsonify({
            'message': 'Response sent successfully',
            'response_message': response_msg.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to respond to support message', 'error': str(e)}), 500

@admin_bp.route('/withdrawals', methods=['GET'])
@jwt_required()
def get_pending_withdrawals():
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', 'pending')  # Default to pending withdrawals
        
        # Query for withdrawal transactions
        query = Transaction.query.filter_by(type=TransactionType.POINT_WITHDRAWAL)
        
        if status:
            query = query.filter_by(status=TransactionStatus(status))
        
        withdrawals = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get user details for each withdrawal
        withdrawal_data = []
        for withdrawal in withdrawals.items:
            user = User.query.get(withdrawal.user_id)
            withdrawal_data.append({
                'transaction': withdrawal.to_dict(),
                'user': user.to_dict() if user else None
            })
        
        return jsonify({
            'withdrawals': withdrawal_data,
            'total': withdrawals.total,
            'pages': withdrawals.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch withdrawals', 'error': str(e)}), 500

@admin_bp.route('/withdrawals/<int:transaction_id>/approve', methods=['POST'])
@jwt_required()
def approve_withdrawal(transaction_id):
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        # Validate transaction ID
        if not isinstance(transaction_id, int) or transaction_id <= 0:
            return jsonify({'message': 'Invalid transaction ID'}), 400
        
        # Get the transaction
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'message': 'Transaction not found'}), 404
        
        if transaction.type != TransactionType.POINT_WITHDRAWAL:
            return jsonify({'message': 'Transaction is not a withdrawal request'}), 400
        
        if transaction.status != TransactionStatus.PENDING:
            return jsonify({'message': 'Transaction is not pending approval'}), 400
        
        # Get the user
        user = User.query.get(transaction.user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Update transaction status to completed
        transaction.status = TransactionStatus.COMPLETED
        transaction.updated_at = db.func.current_timestamp()
        
        db.session.commit()
        
        # Send email notification
        emailer = Emailer()
        email_sent = emailer.send_withdrawal_approved_notification(
            user_email=user.email,
            user_name=user.full_name,
            points=abs(transaction.points_amount),
            amount=abs(transaction.amount),
            method=get_method_from_description(transaction.description)
        )
        
        # Log email sending status (for debugging)
        if not email_sent:
            print(f"Warning: Failed to send withdrawal approval email to {user.email}")
        
        return jsonify({
            'message': 'Withdrawal approved successfully',
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error approving withdrawal: {str(e)}")
        
        # Attempt to rollback any changes if session is still active
        try:
            db.session.rollback()
        except:
            pass
            
        return jsonify({
            'message': 'Failed to approve withdrawal. Please try again later.',
            'error': 'An internal error occurred while processing your request'
        }), 500

@admin_bp.route('/withdrawals/<int:transaction_id>/reject', methods=['POST'])
@jwt_required()
def reject_withdrawal(transaction_id):
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        # Validate transaction ID
        if not isinstance(transaction_id, int) or transaction_id <= 0:
            return jsonify({'message': 'Invalid transaction ID'}), 400
        
        # Get the transaction
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'message': 'Transaction not found'}), 404
        
        if transaction.type != TransactionType.POINT_WITHDRAWAL:
            return jsonify({'message': 'Transaction is not a withdrawal request'}), 400
        
        if transaction.status != TransactionStatus.PENDING:
            return jsonify({'message': 'Transaction is not pending approval'}), 400
        
        # Get the user
        user = User.query.get(transaction.user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Store original values for rollback if needed
        original_balance = user.points_balance
        original_withdrawn_points = user.total_points_withdrawn
        original_withdrawn_amount = user.total_withdrawn
        
        # Validate transaction amounts
        if not isinstance(transaction.points_amount, (int, float)) or not isinstance(transaction.amount, (int, float)):
            return jsonify({'message': 'Invalid transaction amounts'}), 400
        
        # Refund points to user
        user.points_balance -= transaction.points_amount  # points_amount is negative for withdrawals
        user.total_points_withdrawn += transaction.points_amount  # Add back the withdrawn points
        user.total_withdrawn += transaction.amount  # amount is negative for withdrawals
        
        # Validate that the user's balance is not negative after refund
        if user.points_balance < 0:
            # Rollback changes
            user.points_balance = original_balance
            user.total_points_withdrawn = original_withdrawn_points
            user.total_withdrawn = original_withdrawn_amount
            return jsonify({'message': 'Cannot process refund: Invalid user balance'}), 400
        
        # Update transaction status to failed
        transaction.status = TransactionStatus.FAILED
        transaction.updated_at = db.func.current_timestamp()
        
        db.session.commit()
        
        # Send email notification
        emailer = Emailer()
        email_sent = emailer.send_withdrawal_rejected_notification(
            user_email=user.email,
            user_name=user.full_name,
            points=abs(transaction.points_amount),
            amount=abs(transaction.amount),
            method=get_method_from_description(transaction.description),
            reason="Administrative review"
        )
        
        # Log email sending status (for debugging)
        if not email_sent:
            print(f"Warning: Failed to send withdrawal rejection email to {user.email}")
        
        return jsonify({
            'message': 'Withdrawal rejected and points refunded',
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error rejecting withdrawal: {str(e)}")
        
        # Attempt to rollback any changes if session is still active
        try:
            db.session.rollback()
        except:
            pass
            
        return jsonify({
            'message': 'Failed to reject withdrawal. Please try again later.',
            'error': 'An internal error occurred while processing your request'
        }), 500

def get_method_from_description(description):
    """Extract payment method from transaction description"""
    import re
    match = re.search(r'via (\w+)', description)
    return match.group(1) if match else 'unknown'
