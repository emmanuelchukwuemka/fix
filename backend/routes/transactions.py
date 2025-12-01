from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from flask_jwt_extended import jwt_required, get_jwt_identity

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/', methods=['GET'])
@jwt_required()
def get_transactions():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        transaction_type = request.args.get('type')
        
        query = Transaction.query.filter_by(user_id=current_user_id)
        
        if transaction_type:
            try:
                query = query.filter_by(type=TransactionType(transaction_type))
            except ValueError:
                pass  # Invalid transaction type, ignore filter
        
        transactions = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'transactions': [t.to_dict() for t in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch transactions', 'error': str(e)}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    try:
        current_user_id = get_jwt_identity()
        transaction = Transaction.query.filter_by(
            id=transaction_id, 
            user_id=current_user_id
        ).first()
        
        if not transaction:
            return jsonify({'message': 'Transaction not found'}), 404
            
        return jsonify({'transaction': transaction.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch transaction', 'error': str(e)}), 500

@transactions_bp.route('/admin', methods=['GET'])
@jwt_required()
def get_all_transactions():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_id = request.args.get('user_id', type=int)
        transaction_type = request.args.get('type', '')
        
        query = Transaction.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
            
        if transaction_type:
            query = query.filter_by(type=TransactionType(transaction_type))
        
        transactions = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'transactions': [transaction.to_dict() for transaction in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch transactions', 'error': str(e)}), 500

@transactions_bp.route('/admin/<int:transaction_id>/update-status', methods=['PUT'])
@jwt_required()
def update_transaction_status(transaction_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'message': 'Transaction not found'}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'message': 'Status is required'}), 400
        
        # Validate status
        try:
            transaction.status = TransactionStatus(new_status)
        except ValueError:
            return jsonify({'message': 'Invalid status value'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Transaction status updated successfully',
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update transaction status', 'error': str(e)}), 500

@transactions_bp.route('/admin/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_transactions(user_id):
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        transactions = Transaction.query.filter_by(user_id=user_id).order_by(
            Transaction.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        user = User.query.get(user_id)
        
        return jsonify({
            'user': user.to_dict() if user else None,
            'transactions': [transaction.to_dict() for transaction in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch user transactions', 'error': str(e)}), 500

@transactions_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_transaction_summary():
    try:
        current_user_id = get_jwt_identity()
        
        # Calculate totals for different transaction types
        total_earnings = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.EARNING,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        total_withdrawn = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.POINT_WITHDRAWAL,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        total_referral_bonus = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.REFERRAL_BONUS,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        total_code_redemption = db.session.query(db.func.sum(Transaction.points_amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.type == TransactionType.CODE_REDEMPTION,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        return jsonify({
            'total_earnings': abs(total_earnings),
            'total_withdrawn': abs(total_withdrawn),
            'total_referral_bonus': abs(total_referral_bonus),
            'total_code_redemption_points': abs(total_code_redemption)
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch transaction summary', 'error': str(e)}), 500