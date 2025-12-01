from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.task import Task, UserTask
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.models.reward_code import RewardCode
from backend.utils.decorators import partner_restricted
from flask_jwt_extended import jwt_required, get_jwt_identity
import re

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/test', methods=['GET'])
def test_tasks():
    return jsonify({'message': 'Tasks route is working!'}), 200

@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        current_user_id = get_jwt_identity()
        category = request.args.get('category')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Task.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        tasks = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Get user's task status
        user_task_map = {}
        user_tasks = UserTask.query.filter_by(user_id=current_user_id).all()
        for ut in user_tasks:
            user_task_map[ut.task_id] = ut.status
        
        task_list = []
        for task in tasks.items:
            task_dict = task.to_dict()
            task_dict['user_status'] = user_task_map.get(task.id, 'available')
            task_list.append(task_dict)
        
        return jsonify({
            'tasks': task_list,
            'total': tasks.total,
            'pages': tasks.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch tasks', 'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/start', methods=['POST'])
@jwt_required()
@partner_restricted
def start_task(task_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task or not task.is_active:
            return jsonify({'message': 'Task not found or inactive'}), 404
        
        # Check if user already started this task
        user_task = UserTask.query.filter_by(user_id=current_user_id, task_id=task_id).first()
        if user_task and user_task.status != 'available':
            return jsonify({'message': 'Task already started or completed'}), 400
        
        # Create or update user task
        if not user_task:
            user_task = UserTask(
                user_id=current_user_id,
                task_id=task_id,
                status='in_progress'
            )
            db.session.add(user_task)
        else:
            user_task.status = 'in_progress'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Task started successfully',
            'task': task.to_dict(),
            'user_task': user_task.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to start task', 'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/complete', methods=['POST'])
@jwt_required()
@partner_restricted
def complete_task(task_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task or not task.is_active:
            return jsonify({'message': 'Task not found or inactive'}), 404
        
        # Check if user has this task in progress
        user_task = UserTask.query.filter_by(
            user_id=current_user_id, 
            task_id=task_id,
            status='in_progress'
        ).first()
        
        if not user_task:
            return jsonify({'message': 'Task not started or already completed'}), 400
        
        # Mark task as completed
        user_task.status = 'completed'
        user_task.completed_at = db.func.current_timestamp()
        
        # Award points and money to user
        user.points_balance += task.points_reward
        user.total_points_earned += task.points_reward
        user.total_earnings += task.money_reward
        
        # Create transaction record
        transaction = Transaction(
            user_id=current_user_id,
            type=TransactionType.EARNING,
            status=TransactionStatus.COMPLETED,
            description=f"Completed task: {task.title}",
            amount=task.money_reward,
            points_amount=task.points_reward
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Task completed successfully',
            'points_awarded': task.points_reward,
            'money_awarded': task.money_reward,
            'new_points_balance': user.points_balance,
            'new_total_earnings': user.total_earnings
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to complete task', 'error': str(e)}), 500

@tasks_bp.route('/admin', methods=['POST'])
@jwt_required()
def create_task():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'message': 'Title is required'}), 400
        
        task = Task(
            title=data.get('title'),
            description=data.get('description', ''),
            money_reward=data.get('money_reward', 0.0),
            points_reward=data.get('points_reward', 0.0),
            category=data.get('category', 'General'),
            time_required=data.get('time_required', 0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Failed to create task', 'error': str(e)}), 500

@tasks_bp.route('/admin/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Task not found'}), 404
        
        data = request.get_json()
        
        # Update task fields
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.money_reward = data.get('money_reward', task.money_reward)
        task.points_reward = data.get('points_reward', task.points_reward)
        task.category = data.get('category', task.category)
        task.time_required = data.get('time_required', task.time_required)
        task.is_active = data.get('is_active', task.is_active)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update task', 'error': str(e)}), 500

@tasks_bp.route('/admin/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Task not found'}), 404
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Task deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to delete task', 'error': str(e)}), 500

@tasks_bp.route('/admin', methods=['GET'])
@jwt_required()
def get_all_tasks():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category', '')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = Task.query
        
        if category:
            query = query.filter_by(category=category)
            
        if active_only:
            query = query.filter_by(is_active=True)
        
        tasks = query.order_by(Task.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks.items],
            'total': tasks.total,
            'pages': tasks.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch tasks', 'error': str(e)}), 500

@tasks_bp.route('/daily/upload-codes', methods=['POST'])
@jwt_required()
@partner_restricted
def upload_daily_codes():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        codes = data.get('codes', [])
        
        if not codes or not isinstance(codes, list):
            return jsonify({'message': 'Codes array is required'}), 400
        
        # Validate code format and check if they exist
        valid_codes = []
        invalid_codes = []
        
        for code_str in codes:
            # Validate format: 5 uppercase letters + 3 digits
            if not re.match(r'^[A-Z]{5}[0-9]{3}$', code_str):
                invalid_codes.append({'code': code_str, 'reason': 'Invalid format'})
                continue
            
            # Check if code exists and is unused
            code = RewardCode.query.filter_by(code=code_str, is_used=False).first()
            if not code:
                invalid_codes.append({'code': code_str, 'reason': 'Code not found or already used'})
                continue
            
            valid_codes.append(code)
        
        # Process valid codes
        points_earned = 0
        for code in valid_codes:
            # Mark code as used
            code.is_used = True
            code.used_by = current_user_id
            code.used_at = db.func.current_timestamp()
            
            # Add points to user
            user.points_balance += code.point_value
            user.total_points_earned += code.point_value
            points_earned += code.point_value
        
        # Check if user completed daily requirement (5 or 10 codes)
        daily_requirement = getattr(user, 'daily_code_requirement', 5)  # Default to 5
        extra_points = 0
        
        if len(valid_codes) >= daily_requirement:
            # Award extra 2 points for completing daily requirement
            extra_points = 2.0
            user.points_balance += extra_points
            user.total_points_earned += extra_points
            
            # Create transaction for extra points
            extra_transaction = Transaction(
                user_id=current_user_id,
                type=TransactionType.EARNING,
                status=TransactionStatus.COMPLETED,
                description=f"Daily code upload bonus for {len(valid_codes)} codes",
                amount=0,
                points_amount=extra_points
            )
            db.session.add(extra_transaction)
        
        # Create transactions for each redeemed code
        for code in valid_codes:
            transaction = Transaction(
                user_id=current_user_id,
                type=TransactionType.CODE_REDEMPTION,
                status=TransactionStatus.COMPLETED,
                description=f"Redeemed code {code.code}",
                amount=0,
                points_amount=code.point_value,
                reference_id=code.id
            )
            db.session.add(transaction)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully processed {len(valid_codes)} codes',
            'valid_codes': len(valid_codes),
            'invalid_codes': invalid_codes,
            'points_earned': points_earned,
            'extra_points': extra_points,
            'total_points': points_earned + extra_points,
            'new_balance': user.points_balance
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to process codes', 'error': str(e)}), 500

@tasks_bp.route('/daily/set-requirement', methods=['POST'])
@jwt_required()
def set_daily_requirement():
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        requirement = data.get('requirement', 5)
        
        if not user_id:
            return jsonify({'message': 'User ID is required'}), 400
        
        if requirement not in [5, 10]:
            return jsonify({'message': 'Requirement must be 5 or 10'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Set daily requirement (we'll store this in a custom attribute for now)
        # In a real implementation, you might want to create a separate table for user preferences
        user.daily_code_requirement = requirement
        
        db.session.commit()
        
        return jsonify({
            'message': f'Daily code requirement set to {requirement} for user {user.full_name}'
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to set daily requirement', 'error': str(e)}), 500
