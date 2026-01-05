from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models.user import User, UserRole
from backend.models.task import Task, UserTask
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.models.reward_code import RewardCode
from backend.utils.decorators import partner_restricted
from backend.utils.admin_auth import admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity
import re
import os
import time
from werkzeug.utils import secure_filename
from backend.models.notification import Notification, NotificationType

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        current_user_id = int(get_jwt_identity())
        category = request.args.get('category')
        page = request.args.get('page', 1, type=int)
        
        if category:
            query = Task.query.filter_by(is_active=True, category=category).order_by(Task.created_at.desc())
        else:
            query = Task.query.filter_by(is_active=True).order_by(Task.created_at.desc())
        
        per_page = request.args.get('per_page', 100, type=int)
        tasks = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Get user's task status - get ALL user tasks for this user (not just for the current page)
        user_tasks = UserTask.query.filter_by(user_id=current_user_id).all()
        
        user_task_map = {}
        for ut in user_tasks:
            user_task_map[ut.task_id] = ut.status
        
        task_list = []
        for task in tasks.items:
            task_dict = task.to_dict()
            task_dict['user_status'] = user_task_map.get(task.id, 'available')
            task_list.append(task_dict)
        
        # Get all distinct categories for active tasks for the filter tabs
        categories = db.session.query(Task.category).filter(Task.is_active == True).distinct().all()
        category_list = [c[0] for c in categories if c[0]]
        
        return jsonify({
            'tasks': task_list,
            'total': tasks.total,
            'pages': tasks.pages,
            'current_page': page,
            'categories': category_list
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch tasks', 'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/start', methods=['POST'])
@jwt_required()
def start_task(task_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task or not task.is_active:
            return jsonify({'message': 'Task not found or inactive'}), 404
        
        # Check if user already started this task
        user_task = UserTask.query.filter_by(user_id=current_user_id, task_id=task_id).first()
        
        if user_task:
            if user_task.status == 'in_progress':
                return jsonify({
                    'message': 'Task already in progress',
                    'task': task.to_dict(),
                    'user_task': user_task.to_dict()
                }), 200
            
            if user_task.status in ['available', 'rejected']:
                user_task.status = 'in_progress'
                user_task.updated_at = db.func.current_timestamp()
            else:
                return jsonify({
                    'message': f'Task already {user_task.status.replace("_", " ")}',
                    'current_status': user_task.status
                }), 400
        else:
            # Create new user task
            user_task = UserTask(
                user_id=current_user_id,
                task_id=task_id,
                status='in_progress'
            )
            db.session.add(user_task)
        
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
        current_user_id = int(get_jwt_identity())
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
        
        # Handle both JSON and form data (for file uploads)
        if request.is_json:
            data = request.get_json() or {}
            proof_text = data.get('proof_text', '')
            proof_image = data.get('proof_image', '')
        else:
            # Handle form data with file upload
            proof_text = request.form.get('proof_text', '')
            proof_image_file = request.files.get('proof_image')
            proof_image = None
            
            if proof_image_file and proof_image_file.filename != '':
                # Create upload directory if it doesn't exist
                upload_dir = os.path.join('uploads', 'task_proofs')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Secure filename and save file
                filename = secure_filename(proof_image_file.filename)
                file_ext = os.path.splitext(filename)[1]
                
                # Create unique filename using user_id and timestamp
                unique_filename = f"user_{current_user_id}_task_{task_id}_{int(time.time())}{file_ext}"
                filepath = os.path.join(upload_dir, unique_filename)
                
                proof_image_file.save(filepath)
                proof_image = f"/uploads/task_proofs/{unique_filename}"
        
        # Check if task requires admin verification
        if task.requires_admin_verification:
            # For tasks requiring admin verification, we just mark it as pending review
            # and notify the admin
            user_task.status = 'pending_review'
            user_task.completed_at = db.func.current_timestamp()
            user_task.proof_text = proof_text
            user_task.proof_image = proof_image
            
            # Create notification for admin
            admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
            for admin in admin_users:
                notification = Notification(
                    user_id=admin.id,
                    title="Task Completion Pending Review",
                    message=f"User {user.full_name} has completed the task '{task.title}' and is awaiting your review.",
                    type=NotificationType.INFO
                )
                db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'message': 'Task submitted for admin review',
                'status': 'pending_review',
                'task': task.to_dict()
            }), 200
        else:
            # For regular tasks, proceed with immediate completion
            user_task.status = 'completed'
            user_task.completed_at = db.func.current_timestamp()
            
            # Award points and Reward to user
            raw_points = int(task.points_reward)  # Ensure points is an integer
            points_to_add = max(1, raw_points)  # Ensure at least 1 point if any points are awarded
            user.points_balance += points_to_add
            user.total_points_earned += points_to_add
            user.total_earnings += task.reward_amount
            
            # Create transaction record
            transaction = Transaction(
                user_id=current_user_id,
                type=TransactionType.EARNING,
                status=TransactionStatus.COMPLETED,
                description=f"Completed task: {task.title}",
                amount=task.reward_amount,
                points_amount=points_to_add  # Use integer value
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({
                'message': 'Task completed successfully',
                'points_awarded': task.points_reward,
                'reward_awarded': task.reward_amount,
                'new_points_balance': user.points_balance,
                'new_total_earnings': user.total_earnings
            }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to complete task', 'error': str(e)}), 500

@tasks_bp.route('/admin', methods=['POST'])
@admin_required
def create_task():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'message': 'Title is required'}), 400
        
        task = Task(
            title=data.get('title'),
            description=data.get('description', ''),
            reward_amount=data.get('reward_amount', 0.0),
            points_reward=int(data.get('points_reward', 0)),  # Ensure points is an integer
            category=data.get('category', 'General'),
            time_required=data.get('time_required', 0),
            is_active=data.get('is_active', True),
            requires_admin_verification=data.get('requires_admin_verification', False)
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Refresh the task object to ensure all data is current
        db.session.refresh(task)
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({'message': 'Failed to create task', 'error': str(e)}), 500

@tasks_bp.route('/admin/<int:task_id>', methods=['PUT'])
@admin_required
def update_task(task_id):
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Task not found'}), 404
        
        data = request.get_json()
        
        # Update task fields
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.reward_amount = data.get('reward_amount', task.reward_amount)
        task.points_reward = int(data.get('points_reward', task.points_reward))  # Ensure points is an integer
        task.category = data.get('category', task.category)
        task.time_required = data.get('time_required', task.time_required)
        task.is_active = data.get('is_active', task.is_active)
        task.requires_admin_verification = data.get('requires_admin_verification', task.requires_admin_verification)  # New field
        
        db.session.commit()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update task', 'error': str(e)}), 500

@tasks_bp.route('/admin/<int:task_id>', methods=['PUT', 'DELETE'])
@admin_required
def manage_task(task_id):
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Task not found'}), 404
            
        if request.method == 'DELETE':
            # Check if any user_tasks are associated
            user_tasks = UserTask.query.filter_by(task_id=task_id).all()
            for ut in user_tasks:
                db.session.delete(ut)
            
            db.session.delete(task)
            db.session.commit()
            return jsonify({'message': 'Task deleted successfully'}), 200
            
        if request.method == 'PUT':
            data = request.get_json()
            if 'is_active' in data:
                task.is_active = data['is_active']
            if 'title' in data:
                task.title = data['title']
            if 'description' in data:
                task.description = data['description']
            if 'reward_amount' in data:
                task.reward_amount = float(data['reward_amount'])
            if 'points_reward' in data:
                task.points_reward = float(data['points_reward'])
            if 'category' in data:
                task.category = data['category']
                
            db.session.commit()
            return jsonify({'message': 'Task updated successfully', 'task': task.to_dict()}), 200
            
    except Exception as e:
        return jsonify({'message': 'Operation failed', 'error': str(e)}), 500

@tasks_bp.route('/admin', methods=['GET'])
@admin_required
def get_all_tasks_for_admin():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
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
        
        print(f"Admin fetching {len(tasks.items)} tasks, total: {tasks.total}")  # Debug print
        
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
        current_user_id = int(get_jwt_identity())
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
            
            # Add points to user (round to nearest integer and ensure at least 1)
            raw_code_points = round(code.point_value)
            code_points = max(1, raw_code_points)  # Ensure at least 1 point if any points are awarded
            user.points_balance += code_points
            user.total_points_earned += code_points
            points_earned += code_points
        
        # Check if user completed daily requirement (5 or 10 codes)
        daily_requirement = getattr(user, 'daily_code_requirement', 5)  # Default to 5
        extra_points = 0
        
        if len(valid_codes) >= daily_requirement:
            # Award extra 2 points for completing daily requirement
            raw_extra_points = int(2)  # Ensure integer value
            extra_points = max(1, raw_extra_points)  # Ensure at least 1 point if any points are awarded
            user.points_balance += extra_points
            user.total_points_earned += extra_points
            
            # Create transaction for extra points
            extra_transaction = Transaction(
                user_id=current_user_id,
                type=TransactionType.EARNING,
                status=TransactionStatus.COMPLETED,
                description=f"Daily code upload bonus for {len(valid_codes)} codes",
                amount=0,
                points_amount=extra_points  # Use integer value
            )
            db.session.add(extra_transaction)
        
        # Create transactions for each redeemed code
        for code in valid_codes:
            raw_code_points = round(code.point_value)  # Round to nearest integer
            code_points = max(1, raw_code_points)  # Ensure at least 1 point if any points are awarded
            transaction = Transaction(
                user_id=current_user_id,
                type=TransactionType.CODE_REDEMPTION,
                status=TransactionStatus.COMPLETED,
                description=f"Redeemed code {code.code}",
                amount=0,
                points_amount=code_points,  # Use integer value
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
@admin_required
def set_daily_requirement():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
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

@tasks_bp.route('/admin/<int:task_id>/complete', methods=['POST'])
@admin_required
def admin_complete_task(task_id):
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'message': 'User ID is required'}), 400
        
        # Check if task exists
        task = Task.query.get(task_id)
        if not task or not task.is_active:
            return jsonify({'message': 'Task not found or inactive'}), 404
        
        # Check if user has this task pending review
        user_task = UserTask.query.filter_by(
            user_id=user_id, 
            task_id=task_id,
            status='pending_review'
        ).first()
        
        if not user_task:
            return jsonify({'message': 'Task not pending review'}), 400
        
        # Mark task as completed
        user_task.status = 'completed'
        user_task.completed_at = db.func.current_timestamp()
        
        # Get the user who completed the task
        user = User.query.get(user_id)
        
        # Award points and Reward to user
        raw_points = int(task.points_reward)  # Ensure points is an integer
        points_to_add = max(1, raw_points)  # Ensure at least 1 point if any points are awarded
        user.points_balance += points_to_add
        user.total_points_earned += points_to_add
        user.total_earnings += task.reward_amount
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            type=TransactionType.EARNING,
            status=TransactionStatus.COMPLETED,
            description=f"Completed task: {task.title}",
            amount=task.reward_amount,
            points_amount=points_to_add  # Use integer value
        )
        
        # Create notification for the user
        notification = Notification(
            user_id=user_id,
            title="Task Completed!",
            message=f"Congratulations! Your completion of the task '{task.title}' has been verified by admin and you've earned {task.points_reward} points.",
            type=NotificationType.SUCCESS
        )
        
        db.session.add(transaction)
        db.session.add(notification)
        db.session.commit()
        
        # Optionally send email notification
        try:
            from backend.utils.emailer import send_email
            user_email = user.email
            email_subject = "Task Approval Notification - MyFigPoint"
            email_body = f"Hello {user.full_name},\n\nYour task '{task.title}' has been approved by an administrator. You have earned {task.points_reward} points.\n\nThank you for using MyFigPoint!"
            send_email(user_email, email_subject, email_body)
        except Exception as email_error:
            # If email fails, log the error but don't fail the entire operation
            print(f"Failed to send email notification: {str(email_error)}")
        
        # Create notification for admin (task completion confirmation)
        admin_notification = Notification(
            user_id=current_user_id,
            title="Task Verified",
            message=f"You've successfully verified and rewarded {user.full_name} for completing the task '{task.title}'.",
            type=NotificationType.INFO
        )
        db.session.add(admin_notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Task completed and reward awarded successfully',
            'points_awarded': task.points_reward,
            'reward_awarded': task.reward_amount,
            'user_notified': True
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to complete task', 'error': str(e)}), 500

@tasks_bp.route('/admin/completed-tasks', methods=['GET'])
@admin_required
def get_completed_tasks_for_review():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get tasks that are pending review
        user_tasks = UserTask.query.filter_by(status='pending_review').paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for user_task in user_tasks.items:
            task = Task.query.get(user_task.task_id)
            user = User.query.get(user_task.user_id)
            
            result.append({
                'user_task_id': user_task.id,
                'task': task.to_dict() if task else None,
                'user': user.to_dict() if user else None,
                'started_at': user_task.created_at.isoformat() if user_task.created_at else None,
                'submitted_at': user_task.completed_at.isoformat() if user_task.completed_at else None
            })
        
        return jsonify({
            'tasks_for_review': result,
            'total': user_tasks.total,
            'pages': user_tasks.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch tasks for review', 'error': str(e)}), 500

@tasks_bp.route('/admin/review-history', methods=['GET'])
@admin_required
def get_task_review_history():
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get recently completed tasks
        user_tasks = UserTask.query.filter_by(status='completed').order_by(
            UserTask.completed_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for user_task in user_tasks.items:
            task = Task.query.get(user_task.task_id)
            user = User.query.get(user_task.user_id)
            
            result.append({
                'user_task_id': user_task.id,
                'task': task.to_dict() if task else None,
                'user': user.to_dict() if user else None,
                'completed_at': user_task.completed_at.isoformat() if user_task.completed_at else None,
                'started_at': user_task.created_at.isoformat() if user_task.created_at else None
            })
        
        return jsonify({
            'review_history': result,
            'total': user_tasks.total,
            'pages': user_tasks.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch review history', 'error': str(e)}), 500

@tasks_bp.route('/admin/<int:user_task_id>/reject', methods=['POST'])
@admin_required
def admin_reject_task(user_task_id):
    try:
        current_user_id = int(get_jwt_identity())
        admin_user = User.query.get(current_user_id)
        
        data = request.get_json()
        reason = data.get('reason', 'Task requirements not met')
        
        # Get the user task
        user_task = UserTask.query.get(user_task_id)
        if not user_task or user_task.status != 'pending_review':
            return jsonify({'message': 'Task not found or not pending review'}), 404
        
        # Mark task as rejected
        user_task.status = 'rejected'
        
        # Get the user who submitted the task
        user = User.query.get(user_task.user_id)
        task = Task.query.get(user_task.task_id)
        
        # Create notification for the user
        notification = Notification(
            user_id=user.id,
            title="Task Rejected",
            message=f"Your completion of the task '{task.title}' was rejected. Reason: {reason}",
            type=NotificationType.WARNING
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Optionally send email notification
        try:
            from backend.utils.emailer import send_email
            user_email = user.email
            email_subject = "Task Rejection Notification - MyFigPoint"
            email_body = f"Hello {user.full_name},\n\nYour task '{task.title}' has been rejected by an administrator. Reason: {reason}\n\nThank you for using MyFigPoint!"
            send_email(user_email, email_subject, email_body)
        except Exception as email_error:
            # If email fails, log the error but don't fail the entire operation
            print(f"Failed to send email notification: {str(email_error)}")
        
        return jsonify({
            'message': 'Task rejected successfully',
            'user_notified': True
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to reject task', 'error': str(e)}), 500

@tasks_bp.route('/user/rejected-tasks', methods=['GET'])
@jwt_required()
def get_rejected_tasks():
    try:
        current_user_id = int(get_jwt_identity())
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get tasks that were rejected for this user
        user_tasks = UserTask.query.filter_by(
            user_id=current_user_id, 
            status='rejected'
        ).order_by(UserTask.completed_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for user_task in user_tasks.items:
            task = Task.query.get(user_task.task_id)
            
            result.append({
                'user_task_id': user_task.id,
                'task': task.to_dict() if task else None,
                'rejected_at': user_task.completed_at.isoformat() if user_task.completed_at else None
            })
        
        return jsonify({
            'rejected_tasks': result,
            'total': user_tasks.total,
            'pages': user_tasks.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch rejected tasks', 'error': str(e)}), 500
