from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from google.cloud import ndb
from google.cloud import datastore
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Initialize NDB client
def create_ndb_client():
    """Create and return an NDB client for the emulator"""
    os.environ['DATASTORE_EMULATOR_HOST'] = os.getenv('DATASTORE_EMULATOR_HOST', 'localhost:8081')
    os.environ['GOOGLE_CLOUD_PROJECT'] = os.getenv('GOOGLE_CLOUD_PROJECT', 'test-project')
    
    client = ndb.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    return client

# Initialize Datastore client for direct queries
def create_datastore_client():
    """Create and return a Datastore client for the emulator"""
    os.environ['DATASTORE_EMULATOR_HOST'] = os.getenv('DATASTORE_EMULATOR_HOST', 'localhost:8081')
    os.environ['GOOGLE_CLOUD_PROJECT'] = os.getenv('GOOGLE_CLOUD_PROJECT', 'test-project')
    
    client = datastore.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    return client

@app.route('/')
def index():
    """Main page showing all kinds/tables"""
    try:
        client = create_datastore_client()
        
        # Query for all kinds
        query = client.query()
        query.keys_only()
        
        kinds = set()
        for entity in query.fetch():
            kinds.add(entity.key.kind)
        
        kinds = sorted(list(kinds))
        
        return render_template('index.html', kinds=kinds)
    except Exception as e:
        flash(f'Error connecting to datastore: {str(e)}', 'error')
        return render_template('index.html', kinds=[])

@app.route('/kind/<kind_name>')
def browse_kind(kind_name):
    """Browse entities of a specific kind"""
    try:
        client = create_datastore_client()
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Create query for the specific kind
        query = client.query(kind=kind_name)
        
        # Count total entities (for pagination)
        count_query = client.query(kind=kind_name)
        count_query.keys_only()
        total_count = len(list(count_query.fetch()))
        
        # Fetch entities with pagination
        offset = (page - 1) * per_page
        entities = list(query.fetch(limit=per_page, offset=offset))
        
        # Convert entities to dictionaries for display
        entity_data = []
        for entity in entities:
            entity_dict = dict(entity)
            entity_dict['__key__'] = str(entity.key)
            entity_dict['__id__'] = entity.key.id if entity.key.id else entity.key.name
            entity_data.append(entity_dict)
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('browse_kind.html', 
                             kind_name=kind_name,
                             entities=entity_data,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next)
    except Exception as e:
        flash(f'Error browsing {kind_name}: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/kind/<kind_name>/entity/<entity_id>')
def view_entity(kind_name, entity_id):
    """View a specific entity"""
    try:
        client = create_datastore_client()
        
        # Try to parse entity_id as int, fallback to string
        try:
            key = client.key(kind_name, int(entity_id))
        except ValueError:
            key = client.key(kind_name, entity_id)
        
        entity = client.get(key)
        
        if entity is None:
            flash(f'Entity not found: {entity_id}', 'error')
            return redirect(url_for('browse_kind', kind_name=kind_name))
        
        entity_dict = dict(entity)
        entity_dict['__key__'] = str(entity.key)
        entity_dict['__id__'] = entity.key.id if entity.key.id else entity.key.name
        entity_dict['__kind__'] = entity.key.kind
        
        return render_template('view_entity.html', 
                             kind_name=kind_name,
                             entity_id=entity_id,
                             entity=entity_dict)
    except Exception as e:
        flash(f'Error viewing entity: {str(e)}', 'error')
        return redirect(url_for('browse_kind', kind_name=kind_name))

@app.route('/kind/<kind_name>/entity/<entity_id>/edit', methods=['GET', 'POST'])
def edit_entity(kind_name, entity_id):
    """Edit a specific entity"""
    try:
        client = create_datastore_client()
        
        # Try to parse entity_id as int, fallback to string
        try:
            key = client.key(kind_name, int(entity_id))
        except ValueError:
            key = client.key(kind_name, entity_id)
        
        if request.method == 'GET':
            entity = client.get(key)
            
            if entity is None:
                flash(f'Entity not found: {entity_id}', 'error')
                return redirect(url_for('browse_kind', kind_name=kind_name))
            
            entity_dict = dict(entity)
            entity_dict['__key__'] = str(entity.key)
            entity_dict['__id__'] = entity.key.id if entity.key.id else entity.key.name
            
            return render_template('edit_entity.html', 
                                 kind_name=kind_name,
                                 entity_id=entity_id,
                                 entity=entity_dict)
        
        elif request.method == 'POST':
            # Get the entity
            entity = client.get(key)
            
            if entity is None:
                flash(f'Entity not found: {entity_id}', 'error')
                return redirect(url_for('browse_kind', kind_name=kind_name))
            
            # Update entity properties from form data
            for field_name, field_value in request.form.items():
                if field_name.startswith('__'):
                    continue  # Skip internal fields
                
                # Try to parse value as JSON for complex types
                try:
                    parsed_value = json.loads(field_value)
                    entity[field_name] = parsed_value
                except json.JSONDecodeError:
                    # If not JSON, treat as string
                    entity[field_name] = field_value
            
            # Save the entity
            client.put(entity)
            
            flash(f'Entity {entity_id} updated successfully!', 'success')
            return redirect(url_for('view_entity', kind_name=kind_name, entity_id=entity_id))
    
    except Exception as e:
        flash(f'Error editing entity: {str(e)}', 'error')
        return redirect(url_for('browse_kind', kind_name=kind_name))

@app.route('/kind/<kind_name>/new', methods=['GET', 'POST'])
def new_entity(kind_name):
    """Create a new entity"""
    try:
        client = create_datastore_client()
        
        if request.method == 'GET':
            return render_template('new_entity.html', kind_name=kind_name)
        
        elif request.method == 'POST':
            # Get entity ID from form
            entity_id = request.form.get('entity_id')
            
            # Create key
            if entity_id:
                try:
                    key = client.key(kind_name, int(entity_id))
                except ValueError:
                    key = client.key(kind_name, entity_id)
            else:
                key = client.key(kind_name)
            
            # Create new entity
            entity = datastore.Entity(key=key)
            
            # Set properties from form data
            for field_name, field_value in request.form.items():
                if field_name in ['entity_id']:
                    continue  # Skip special fields
                
                if field_value:  # Only add non-empty values
                    # Try to parse value as JSON for complex types
                    try:
                        parsed_value = json.loads(field_value)
                        entity[field_name] = parsed_value
                    except json.JSONDecodeError:
                        # If not JSON, treat as string
                        entity[field_name] = field_value
            
            # Save the entity
            client.put(entity)
            
            actual_id = entity.key.id if entity.key.id else entity.key.name
            flash(f'Entity created successfully with ID: {actual_id}', 'success')
            return redirect(url_for('view_entity', kind_name=kind_name, entity_id=actual_id))
    
    except Exception as e:
        flash(f'Error creating entity: {str(e)}', 'error')
        return redirect(url_for('browse_kind', kind_name=kind_name))

@app.route('/kind/<kind_name>/entity/<entity_id>/delete', methods=['POST'])
def delete_entity(kind_name, entity_id):
    """Delete a specific entity"""
    try:
        client = create_datastore_client()
        
        # Try to parse entity_id as int, fallback to string
        try:
            key = client.key(kind_name, int(entity_id))
        except ValueError:
            key = client.key(kind_name, entity_id)
        
        # Delete the entity
        client.delete(key)
        
        flash(f'Entity {entity_id} deleted successfully!', 'success')
        return redirect(url_for('browse_kind', kind_name=kind_name))
    
    except Exception as e:
        flash(f'Error deleting entity: {str(e)}', 'error')
        return redirect(url_for('browse_kind', kind_name=kind_name))

@app.route('/api/kinds')
def api_kinds():
    """API endpoint to get all kinds"""
    try:
        client = create_datastore_client()
        
        query = client.query()
        query.keys_only()
        
        kinds = set()
        for entity in query.fetch():
            kinds.add(entity.key.kind)
        
        return jsonify(list(kinds))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def format_value(value):
    """Format value for display in templates"""
    if isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)
    else:
        return str(value)

# Add template filter
app.jinja_env.filters['format_value'] = format_value

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
