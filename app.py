import os
import time
import random
from flask import Flask, jsonify, request, send_from_directory
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file (if exists)
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')

# ============================================================
# DATABASE SETUP (MongoDB)
# ============================================================
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)

# Use 'bizflow' database
db = client['bizflow']

# ============================================================
# VALID CATEGORIES (collection names)
# ============================================================
VALID_CATEGORIES = ['sales', 'subs', 'expenses', 'customers', 'funnel']

def generate_id():
    """Generate a unique ID similar to the JS version."""
    return time.time() * 1000 + random.random()

def format_doc(doc):
    """Format MongoDB document to standard JSON dictionary."""
    if doc:
        # Remove MongoDB's internal _id field from the response
        doc.pop('_id', None)
    return doc

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def serve_index():
    """Serve the main dashboard page."""
    return send_from_directory('static', 'index.html')

@app.route('/api/all', methods=['GET'])
def get_all_data():
    """Return all data from all collections."""
    result = {}
    try:
        for cat in VALID_CATEGORIES:
            collection = db[cat]
            docs = list(collection.find({}))
            result[cat] = [format_doc(d) for d in docs]
        return jsonify(result)
    except Exception as e:
        print("Database error:", e)
        return jsonify({'error': 'Failed to connect to database. Ensure MONGO_URI is set correctly.'}), 500

@app.route('/api/<category>', methods=['POST'])
def add_record(category):
    """Add or update a record to the specified category collection."""
    if category not in VALID_CATEGORIES:
        return jsonify({'error': f'Invalid category: {category}'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    # Generate ID if not provided by frontend
    if 'id' not in data or data['id'] is None:
        data['id'] = generate_id()
    
    # Store frontend's id as a proper float
    data['id'] = float(data['id'])

    # Map 'desc' to 'description' for expenses (frontend uses 'desc')
    if category == 'expenses' and 'desc' in data:
        data['description'] = data.pop('desc')

    # Convert booleans for customers table
    if category == 'customers':
        if 'product' in data:
            data['product'] = bool(data['product'])
        if 'sub' in data:
            data['sub'] = bool(data['sub'])

    collection = db[category]
    try:
        # Use update_one with upsert=True to either insert or update
        # We query by the frontend 'id'
        collection.update_one({'id': data['id']}, {'$set': data}, upsert=True)
        
        # Fetch the saved record
        saved_doc = collection.find_one({'id': data['id']})
        return jsonify(format_doc(saved_doc)), 201
    except Exception as e:
        print("Database error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/<category>/<float:record_id>', methods=['DELETE'])
def delete_record(category, record_id):
    """Delete a record by ID from the specified category collection."""
    if category not in VALID_CATEGORIES:
        return jsonify({'error': f'Invalid category: {category}'}), 400

    collection = db[category]
    try:
        result = collection.delete_one({'id': record_id})
        
        if result.deleted_count > 0:
            return jsonify({'success': True, 'deleted': record_id})
        else:
            return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        print("Database error:", e)
        return jsonify({'error': str(e)}), 500

# Also handle integer IDs
@app.route('/api/<category>/<int:record_id>', methods=['DELETE'])
def delete_record_int(category, record_id):
    """Delete a record by integer ID."""
    return delete_record(category, float(record_id))

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("=" * 50)
    print("  BizFlow Backend Server (MongoDB)")
    print("  Open http://localhost:5000 in your browser")
    print(f"  MONGO_URI: {MONGO_URI}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
