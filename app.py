from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'message': 'Event Planner API is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
