import os
from flask import Flask, jsonify
from models import db, User, Event, Participant

app = Flask(__name__)

# Database configuration
database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://app_user:app_password@db:3306/event_planner')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'message': 'Event Planner API is running'})

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
