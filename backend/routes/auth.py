from flask import Blueprint, request, jsonify
from backend.app import db, bcrypt
from backend.models.user import User, UserRole
from backend.models.password_reset import PasswordResetToken
from backend.models.transaction import Transaction, TransactionType, TransactionStatus
from backend.utils.helpers import generate_referral_code
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('full_name') or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Full name, email, and password are required'}), 400
        
        # Validate email format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email')):
            return jsonify({'message': 'Invalid email format'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'message': 'Email already registered'}), 409
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
        
        # Create user - only allow user or admin roles during registration
        role = data.get('role', 'user')
        if role == 'partner':
            role = 'user'  # Force partner registrations to user role
        
        user = User(
            full_name=data.get('full_name'),
            email=data.get('email'),
            password_hash=hashed_password,
            role=UserRole(role),
            referral_code=generate_referral_code()
        )
        
        # Set referral if provided
        referrer = None
        if data.get('referral_code'):
            referrer = User.query.filter_by(referral_code=data.get('referral_code')).first()
            if referrer:
                user.referred_by = referrer.id
        
        db.session.add(user)
        db.session.commit()
        
        # Award referral bonus to referrer if applicable
        if referrer:
            # Award 100 points as referral bonus
            bonus_points = 100.0
            referrer.points_balance += bonus_points
            referrer.total_points_earned += bonus_points
            
            # Create referral bonus transaction
            transaction = Transaction(
                user_id=referrer.id,
                type=TransactionType.REFERRAL_BONUS,
                status=TransactionStatus.COMPLETED,
                description=f"Referral bonus for {user.full_name}",
                amount=0,
                points_amount=bonus_points
            )
            
            db.session.add(transaction)
            db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=data.get('email')).first()
        
        if not user or not bcrypt.check_password_hash(user.password_hash, data.get('password')):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch profile', 'error': str(e)}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'message': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists or not for security
            return jsonify({'message': 'If your email is registered, you will receive a password reset link'}), 200
        
        # Create password reset token
        reset_token = PasswordResetToken(user_id=user.id)
        db.session.add(reset_token)
        db.session.commit()
        
        # In a real implementation, you would send an email with the reset link
        # For now, we'll just return the token (not recommended for production)
        return jsonify({
            'message': 'Password reset token generated',
            'token': reset_token.token,
            'expires_at': reset_token.expires_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to process password reset request', 'error': str(e)}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return jsonify({'message': 'Token and new password are required'}), 400
        
        # Validate password strength
        if len(new_password) < 6:
            return jsonify({'message': 'Password must be at least 6 characters long'}), 400
        
        # Find reset token
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset_token:
            return jsonify({'message': 'Invalid or expired reset token'}), 400
        
        if reset_token.is_expired():
            return jsonify({'message': 'Reset token has expired'}), 400
        
        if reset_token.used:
            return jsonify({'message': 'Reset token has already been used'}), 400
        
        # Get user and update password
        user = User.query.get(reset_token.user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Hash new password
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password_hash = hashed_password
        
        # Mark token as used
        reset_token.used = True
        
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to reset password', 'error': str(e)}), 500

# Social Login Routes (Placeholder implementations)
@auth_bp.route('/google', methods=['GET'])
def google_login():
    """
    Placeholder for Google OAuth login.
    In a real implementation, this would redirect to Google's OAuth endpoint.
    """
    return jsonify({
        'message': 'Google login endpoint - In a real implementation, this would redirect to Google OAuth',
        'note': 'For demo purposes, please use email login/signup'
    }), 200

@auth_bp.route('/apple', methods=['GET'])
def apple_login():
    """
    Placeholder for Apple OAuth login.
    In a real implementation, this would redirect to Apple's OAuth endpoint.
    """
    return jsonify({
        'message': 'Apple login endpoint - In a real implementation, this would redirect to Apple OAuth',
        'note': 'For demo purposes, please use email login/signup'
    }), 200

@auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """
    Placeholder for Google OAuth callback.
    In a real implementation, this would handle the OAuth response from Google.
    """
    return jsonify({
        'message': 'Google OAuth callback - In a real implementation, this would handle Google OAuth response',
        'note': 'For demo purposes, please use email login/signup'
    }), 200

@auth_bp.route('/apple/callback', methods=['POST'])
def apple_callback():
    """
    Placeholder for Apple OAuth callback.
    In a real implementation, this would handle the OAuth response from Apple.
    """
    return jsonify({
        'message': 'Apple OAuth callback - In a real implementation, this would handle Apple OAuth response',
        'note': 'For demo purposes, please use email login/signup'
    }), 200
