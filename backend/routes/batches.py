from flask import Blueprint, request, jsonify, send_file
from backend.extensions import db
from backend.models.user import User, UserRole
from backend.models.batch import Batch
from backend.models.reward_code import RewardCode
from backend.utils.helpers import generate_reward_code
from backend.utils.admin_auth import admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity
import csv
import io
from datetime import datetime

batches_bp = Blueprint('batches', __name__)

@batches_bp.route('/', methods=['GET'])
@jwt_required()
@admin_required
def list_batches():
    try:
        batches = Batch.query.order_by(Batch.created_at.desc()).all()
        return jsonify({
            'batches': [batch.to_dict() for batch in batches]
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch batches', 'error': str(e)}), 500

@batches_bp.route('/', methods=['POST'])
@jwt_required()
@admin_required
def create_batch():
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        point_value = float(data.get('point_value', 1.0))
        
        if not name:
            return jsonify({'message': 'Batch name is required'}), 400
            
        batch = Batch(
            name=name,
            description=description,
            point_value=point_value
        )
        db.session.add(batch)
        db.session.commit()
        
        return jsonify({
            'message': 'Batch created successfully',
            'batch': batch.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': 'Failed to create batch', 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_batch(batch_id):
    try:
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'message': 'Batch not found'}), 404
            
        codes = [code.to_dict() for code in batch.codes]
        
        return jsonify({
            'batch': batch.to_dict(),
            'codes': codes
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch batch details', 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_batch(batch_id):
    try:
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'message': 'Batch not found'}), 404
            
        # The relationship is set to cascade delete codes
        db.session.delete(batch)
        db.session.commit()
        
        return jsonify({'message': 'Batch and all associated codes deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to delete batch', 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>/generate', methods=['POST'])
@jwt_required()
@admin_required
def generate_codes_for_batch(batch_id):
    try:
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'message': 'Batch not found'}), 404
            
        data = request.get_json()
        count = int(data.get('count', 10))
        
        if count <= 0 or count > 5000:
            return jsonify({'message': 'Count must be between 1 and 5000'}), 400
            
        codes_list = []
        for _ in range(count):
            code_str = generate_reward_code()
            # Double check if code exists already (rare but possible)
            while RewardCode.query.filter_by(code=code_str).first():
                code_str = generate_reward_code()
                
            reward_code = RewardCode(
                code=code_str,
                point_value=batch.point_value,
                batch_id=batch.id
            )
            db.session.add(reward_code)
            codes_list.append(code_str)
            
        batch.count += count
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully generated {count} codes for batch {batch.name}',
            'count': count
        }), 201
    except Exception as e:
        return jsonify({'message': 'Failed to generate codes', 'error': str(e)}), 500

@batches_bp.route('/<int:batch_id>/export', methods=['GET'])
@jwt_required()
@admin_required
def export_batch(batch_id):
    try:
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'message': 'Batch not found'}), 404
            
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Code', 'Point Value', 'Status', 'Used By', 'Used At', 'Created At'])
        
        for code in batch.codes:
            writer.writerow([
                code.code,
                code.point_value,
                'Used' if code.is_used else 'Available',
                code.used_by or '',
                code.used_at.isoformat() if code.used_at else '',
                code.created_at.isoformat() if code.created_at else ''
            ])
            
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'batch_{batch.name.replace(" ", "_")}.csv'
        )
    except Exception as e:
        return jsonify({'message': 'Failed to export batch', 'error': str(e)}), 500
