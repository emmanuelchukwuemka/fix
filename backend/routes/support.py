from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models.user import User, UserRole
from backend.models.support_message import SupportMessage, MessageType, MessageStatus
from flask_jwt_extended import jwt_required, get_jwt_identity

support_bp = Blueprint('support', __name__)

@support_bp.route('/', methods=['POST'])
@jwt_required()
def create_support_message():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404

        data = request.get_json()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()

        if not subject or not message:
            return jsonify({'message': 'Subject and message are required'}), 400

        if len(subject) > 200:
            return jsonify({'message': 'Subject must be 200 characters or less'}), 400

        # Create support message
        support_message = SupportMessage(
            user_id=current_user_id,
            subject=subject,
            message=message,
            message_type=MessageType.USER_TO_SUPPORT,
            status=MessageStatus.SENT
        )

        db.session.add(support_message)
        db.session.commit()

        return jsonify({
            'message': 'Support message sent successfully',
            'support_message': support_message.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'message': 'Failed to send support message', 'error': str(e)}), 500

@support_bp.route('/', methods=['GET'])
@jwt_required()
def get_support_messages():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        messages = SupportMessage.query.filter_by(user_id=current_user_id).order_by(
            SupportMessage.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'messages': [msg.to_dict() for msg in messages.items],
            'total': messages.total,
            'pages': messages.pages,
            'current_page': page
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch support messages', 'error': str(e)}), 500

@support_bp.route('/<int:message_id>', methods=['GET'])
@jwt_required()
def get_support_message(message_id):
    try:
        current_user_id = get_jwt_identity()
        message = SupportMessage.query.filter_by(
            id=message_id,
            user_id=current_user_id
        ).first()

        if not message:
            return jsonify({'message': 'Support message not found'}), 404

        return jsonify({'message': message.to_dict()}), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch support message', 'error': str(e)}), 500

@support_bp.route('/whatsapp', methods=['GET'])
@jwt_required()
def get_whatsapp_support():
    try:
        # Return WhatsApp support contact info
        return jsonify({
            'whatsapp_number': '+1234567890',  # Replace with actual number
            'message': 'Contact us on WhatsApp for immediate support'
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to get WhatsApp support info', 'error': str(e)}), 500
