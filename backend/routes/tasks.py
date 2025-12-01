from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.task import Task, UserTask
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from flask_jwt_extended import jwt_required, get_jwt_identity

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
