from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.notification import Notification, NotificationType
from flask_jwt_extended import jwt_required, get_jwt_identity

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'

        query = Notification.query.filter_by(user_id=current_user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        notifications = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'notifications': [n.to_dict() for n in notifications.items],
            'total': notifications.total,
            'pages': notifications.pages,
            'current_page': page,
            'unread_count': Notification.query.filter_by(user_id=current_user_id, is_read=False).count()
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch notifications', 'error': str(e)}), 500

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    try:
        current_user_id = get_jwt_identity()
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first()

        if not notification:
            return jsonify({'message': 'Notification not found'}), 404

        notification.is_read = True
        db.session.commit()

        return jsonify({
            'message': 'Notification marked as read',
            'notification': notification.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to mark notification as read', 'error': str(e)}), 500

@notifications_bp.route('/mark-all-read', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    try:
        current_user_id = get_jwt_identity()

        updated_count = Notification.query.filter_by(
            user_id=current_user_id,
            is_read=False
        ).update({'is_read': True})

        db.session.commit()

        return jsonify({
            'message': f'Marked {updated_count} notifications as read'
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to mark notifications as read', 'error': str(e)}), 500

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    try:
        current_user_id = get_jwt_identity()
        unread_count = Notification.query.filter_by(
            user_id=current_user_id,
            is_read=False
        ).count()

        return jsonify({'unread_count': unread_count}), 200

    except Exception as e:
        return jsonify({'message': 'Failed to get unread count', 'error': str(e)}), 500

@notifications_bp.route('/admin/send', methods=['POST'])
@jwt_required()
def send_notification():
    try:
        current_user_id = get_jwt_identity()
        sender = User.query.get(current_user_id)
        
        # Check if user is admin
        if sender.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()
        notification_type = data.get('type', 'info')
        
        if not title or not message:
            return jsonify({'message': 'Title and message are required'}), 400
        
        if user_id:
            # Send to specific user
            user = User.query.get(user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 404
                
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=NotificationType(notification_type)
            )
        else:
            # Send to all users
            users = User.query.all()
            notifications = []
            
            for user in users:
                notification = Notification(
                    user_id=user.id,
                    title=title,
                    message=message,
                    type=NotificationType(notification_type)
                )
                notifications.append(notification)
                
            db.session.add_all(notifications)
            db.session.commit()
            
            return jsonify({
                'message': f'Notification sent to {len(users)} users',
                'notification_count': len(users)
            }), 201
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Notification sent successfully',
            'notification': notification.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Failed to send notification', 'error': str(e)}), 500

@notifications_bp.route('/admin/broadcast', methods=['POST'])
@jwt_required()
def broadcast_notification():
    try:
        current_user_id = get_jwt_identity()
        sender = User.query.get(current_user_id)
        
        # Check if user is admin
        if sender.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()
        notification_type = data.get('type', 'info')
        
        if not title or not message:
            return jsonify({'message': 'Title and message are required'}), 400
        
        # Send to all users
        users = User.query.all()
        notifications = []
        
        for user in users:
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                type=NotificationType(notification_type)
            )
            notifications.append(notification)
            
        db.session.add_all(notifications)
        db.session.commit()
        
        return jsonify({
            'message': f'Broadcast notification sent to {len(users)} users',
            'notification_count': len(users)
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Failed to broadcast notification', 'error': str(e)}), 500

@notifications_bp.route('/admin/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'message': 'Notification not found'}), 404
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'message': 'Notification deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to delete notification', 'error': str(e)}), 500

@notifications_bp.route('/admin/all', methods=['GET'])
@jwt_required()
def get_all_notifications():
    try:
        current_user_id = get_jwt_identity()
        admin_user = User.query.get(current_user_id)
        
        # Check if user is admin
        if admin_user.role != UserRole.ADMIN:
            return jsonify({'message': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_id = request.args.get('user_id', type=int)
        
        query = Notification.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        notifications = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications.items],
            'total': notifications.total,
            'pages': notifications.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch notifications', 'error': str(e)}), 500
