from flask import Blueprint, request, jsonify
from backend.app import db, bcrypt
from backend.models.user import User, UserRole
from backend.models.password_reset import PasswordResetToken
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
        
        # Create user
        user = User(
            full_name=data.get('full_name'),
            email=data.get('email'),
            password_hash=hashed_password,
            role=UserRole(data.get('role', 'user')),
            referral_code=generate_referral_code()
        )
        
        # Set referral if provided
        if data.get('referral_code'):
            referrer = User.query.filter_by(referral_code=data.get('referral_code')).first()
            if referrer:
                user.referred_by = referrer.id
        
        db.session.add(user)
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