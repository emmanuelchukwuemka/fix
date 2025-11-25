from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User
from backend.models.notification import Notification
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
