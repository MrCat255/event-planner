import os
import re
from datetime import timedelta, datetime
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Event, Participant

app = Flask(__name__)

# Database configuration
database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://app_user:app_password@db:3306/event_planner')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'message': 'Event Planner API is running'})

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Password validation
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create new user
        new_user = User(email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['GET'])
@jwt_required()
def get_events():
    try:
        current_user_id = int(get_jwt_identity())
        events = Event.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'events': [event.to_dict() for event in events]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['POST'])
@jwt_required()
def create_event():
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title')
        date_str = data.get('date')
        
        if not title or not date_str:
            return jsonify({'error': 'Title and date are required'}), 400
        
        # Parse date
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use ISO format (e.g., 2024-12-31T10:00:00)'}), 400
        
        # Create event
        new_event = Event(
            title=title,
            date=date,
            user_id=current_user_id
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event created successfully',
            'event': new_event.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    try:
        current_user_id = int(get_jwt_identity())
        event = Event.query.filter_by(id=event_id, user_id=current_user_id).first()
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields
        if 'title' in data:
            event.title = data['title']
        
        if 'date' in data:
            try:
                event.date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use ISO format (e.g., 2024-12-31T10:00:00)'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Event updated successfully',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    try:
        current_user_id = int(get_jwt_identity())
        event = Event.query.filter_by(id=event_id, user_id=current_user_id).first()
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/api/participants', methods=['GET'])
@jwt_required()
def get_participants():
    try:
        current_user_id = int(get_jwt_identity())
        participants = Participant.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'participants': [participant.to_dict() for participant in participants]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/participants', methods=['POST'])
@jwt_required()
def create_participant():
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'event_id is required'}), 400
        
        # Check if event exists and belongs to another user (participant can join any event)
        event = Event.query.filter_by(id=event_id).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if participant already exists
        if Participant.query.filter_by(user_id=current_user_id, event_id=event_id).first():
            return jsonify({'error': 'User is already a participant of this event'}), 409
        
        # Create participant
        new_participant = Participant(
            user_id=current_user_id,
            event_id=event_id
        )
        
        db.session.add(new_participant)
        db.session.commit()
        
        return jsonify({
            'message': 'Participant added successfully',
            'participant': new_participant.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/participants/<int:participant_id>', methods=['PUT'])
@jwt_required()
def update_participant(participant_id):
    try:
        current_user_id = int(get_jwt_identity())
        participant = Participant.query.filter_by(id=participant_id, user_id=current_user_id).first()
        
        if not participant:
            return jsonify({'error': 'Participant not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update event_id if provided
        if 'event_id' in data:
            event_id = data['event_id']
            # Check if event exists
            event = Event.query.filter_by(id=event_id).first()
            if not event:
                return jsonify({'error': 'Event not found'}), 404
            
            # Check if participant already exists for this event
            existing = Participant.query.filter_by(user_id=current_user_id, event_id=event_id).first()
            if existing and existing.id != participant_id:
                return jsonify({'error': 'User is already a participant of this event'}), 409
            
            participant.event_id = event_id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Participant updated successfully',
            'participant': participant.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/participants/<int:participant_id>', methods=['DELETE'])
@jwt_required()
def delete_participant(participant_id):
    try:
        current_user_id = int(get_jwt_identity())
        participant = Participant.query.filter_by(id=participant_id, user_id=current_user_id).first()
        
        if not participant:
            return jsonify({'error': 'Participant not found'}), 404
        
        db.session.delete(participant)
        db.session.commit()
        
        return jsonify({
            'message': 'Participant removed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
