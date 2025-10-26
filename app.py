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

# Store current project in session
def get_current_project():
    """Get the current project from session or environment"""
    from flask import session
    return session.get('current_project', os.getenv('GOOGLE_CLOUD_PROJECT', 'test-project'))

def set_current_project(project_name):
    """Set the current project in session"""
    from flask import session
    session['current_project'] = project_name
    os.environ['GOOGLE_CLOUD_PROJECT'] = project_name

def get_available_projects():
    """Get list of available projects from the datastore emulator"""
    from flask import session
    
    try:
        projects = set()
        
        # Add the current configured project from .env
        env_project = os.getenv('GOOGLE_CLOUD_PROJECT', 'test-project')
        projects.add(env_project)
        
        # Add projects from session (previously used projects)
        if 'known_projects' in session:
            projects.update(session['known_projects'])
        
        # Try to detect projects by attempting connections
        # The emulator stores data per-project, so we'll try common names
        common_projects = [
            'test-project',
            'dev-project', 
            'local-dev',
            'emulator-project',
            'mephysio-hrd-local',
            'me-physio-hrd',
        ]
        
        for proj in common_projects:
            try:
                # Try to connect to each project
                os.environ['GOOGLE_CLOUD_PROJECT'] = proj
                client = datastore.Client(project=proj)
                query = client.query()
                query.keys_only()
                entities = list(query.fetch(limit=1))
                # If we can fetch at least one entity, project has data
                if entities:
                    projects.add(proj)
            except Exception:
                # Project doesn't exist or has no data
                pass
        
        # Store known projects in session
        session['known_projects'] = list(projects)
        
        # Restore original project
        os.environ['GOOGLE_CLOUD_PROJECT'] = get_current_project()
        
        return sorted(list(projects))
    except Exception as e:
        # Fallback to configured project
        return [os.getenv('GOOGLE_CLOUD_PROJECT', 'test-project')]
    except Exception as e:
        # Fallback to configured project
        return [os.getenv('GOOGLE_CLOUD_PROJECT', 'test-project')]

def get_property_type(value):
    """Get the type name of a property value"""
    if value is None:
        return 'null'
    elif isinstance(value, bool):
        return 'boolean'
    elif isinstance(value, int):
        return 'integer'
    elif isinstance(value, float):
        return 'float'
    elif isinstance(value, bytes):
        return 'blob'
    elif isinstance(value, str):
        return 'string'
    elif isinstance(value, list):
        return 'array'
    elif isinstance(value, dict):
        return 'object'
    elif isinstance(value, datetime):
        return 'datetime'
    else:
        # Check for other blob-like types from Google Cloud
        type_name = type(value).__name__
        if 'blob' in type_name.lower() or 'binary' in type_name.lower():
            return 'blob'
        return 'unknown'

def convert_form_value(value, original_type):
    """Convert form value back to its original type"""
    if not value and value != "0" and value != "false":
        return None
    
    try:
        if original_type == 'boolean':
            return value.lower() in ('true', '1', 'on', 'yes')
        elif original_type == 'integer':
            return int(value)
        elif original_type == 'float':
            return float(value)
        elif original_type == 'datetime':
            # Parse ISO format datetime string back to datetime object
            if isinstance(value, str):
                # Handle various datetime formats
                try:
                    # First try full ISO format with timezone
                    return datetime.fromisoformat(value)
                except ValueError:
                    try:
                        # Try with Z suffix (UTC timezone)
                        if value.endswith('Z'):
                            return datetime.fromisoformat(value.replace('Z', '+00:00'))
                        # Try without timezone (assume it's the original timezone)
                        elif 'T' in value:
                            # ISO format without timezone - parse and keep naive
                            return datetime.fromisoformat(value)
                        else:
                            # Try parsing without T separator
                            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # If all else fails, return the original value
                        return value
            return value
        elif original_type == 'blob':
            # Convert base64 string back to bytes
            if isinstance(value, str):
                import base64
                try:
                    return base64.b64decode(value)
                except Exception:
                    # If base64 decode fails, try encoding as UTF-8 bytes
                    return value.encode('utf-8')
            return value
        elif original_type in ['array', 'object']:
            return json.loads(value)
        elif original_type == 'null':
            return None
        else:
            return value  # Keep as string
    except (ValueError, json.JSONDecodeError):
        # If conversion fails, return as string
        return value

def format_value_for_form(value):
    """Format value for display in form fields"""
    if isinstance(value, bool):
        return value  # Will be handled specially in template
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, bytes):
        # Convert bytes to base64 for display in form
        import base64
        return base64.b64encode(value).decode('utf-8')
    elif isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)
    else:
        # Check for other blob-like types
        type_name = type(value).__name__
        if 'blob' in type_name.lower() or 'binary' in type_name.lower():
            import base64
            try:
                # Try to encode as base64
                return base64.b64encode(bytes(value)).decode('utf-8')
            except:
                return str(value)
        return str(value) if value is not None else ""

# Initialize NDB client
def create_ndb_client():
    """Create and return an NDB client for the emulator"""
    os.environ['DATASTORE_EMULATOR_HOST'] = os.getenv('DATASTORE_EMULATOR_HOST', 'localhost:8081')
    os.environ['GOOGLE_CLOUD_PROJECT'] = os.getenv('GOOGLE_CLOUD_PROJECT', 'me-physio-hrd')

    client = ndb.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    return client

# Initialize Datastore client for direct queries
def create_datastore_client():
    """Create and return a Datastore client for the emulator"""
    os.environ['DATASTORE_EMULATOR_HOST'] = os.getenv('DATASTORE_EMULATOR_HOST', 'localhost:8081')
    
    # Use current project from session
    current_project = get_current_project()
    os.environ['GOOGLE_CLOUD_PROJECT'] = current_project
    
    client = datastore.Client(project=current_project)
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
            
            # Store original types for comparison
            original_types = {}
            for prop_name, prop_value in entity.items():
                original_types[prop_name] = get_property_type(prop_value)
            
            # Update entity properties from form data
            for field_name, field_value in request.form.items():
                if field_name.startswith('__') or field_name.endswith('_type'):
                    continue  # Skip internal fields and type fields
                
                # Get the original type for this property
                original_type = original_types.get(field_name, 'string')
                
                # Convert the form value back to its original type
                converted_value = convert_form_value(field_value, original_type)
                entity[field_name] = converted_value
            
            # Handle checkboxes for boolean fields (unchecked checkboxes don't appear in form data)
            for prop_name, original_type in original_types.items():
                if original_type == 'boolean' and prop_name not in request.form:
                    entity[prop_name] = False
            
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
                if field_name in ['entity_id'] or field_name.endswith('_type'):
                    continue  # Skip special fields and type fields
                
                if field_value:  # Only add non-empty values
                    # Get the type for this property
                    type_field = field_name + '_type'
                    property_type = request.form.get(type_field, 'string')
                    
                    # Convert the value to the appropriate type
                    converted_value = convert_form_value(field_value, property_type)
                    entity[field_name] = converted_value
            
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
    elif isinstance(value, bytes):
        # Display blob as base64 with length info
        import base64
        b64_value = base64.b64encode(value).decode('utf-8')
        return f"[Blob: {len(value)} bytes]\n{b64_value[:100]}{'...' if len(b64_value) > 100 else ''}"
    elif isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)
    else:
        # Check for other blob-like types
        type_name = type(value).__name__
        if 'blob' in type_name.lower() or 'binary' in type_name.lower():
            import base64
            try:
                bytes_value = bytes(value)
                b64_value = base64.b64encode(bytes_value).decode('utf-8')
                return f"[Blob: {len(bytes_value)} bytes]\n{b64_value[:100]}{'...' if len(b64_value) > 100 else ''}"
            except:
                return str(value)
        return str(value)

# Add template filters
app.jinja_env.filters['format_value'] = format_value
app.jinja_env.filters['get_type'] = get_property_type
app.jinja_env.filters['format_for_form'] = format_value_for_form

# Context processor to add project info to all templates
@app.context_processor
def inject_project_info():
    """Inject current project and available projects into all templates"""
    return {
        'current_project': get_current_project(),
        'available_projects': get_available_projects()
    }

@app.route('/switch-project', methods=['POST'])
def switch_project():
    """Switch to a different project"""
    project_name = request.form.get('project_name')
    if project_name:
        set_current_project(project_name)
        flash(f'Switched to project: {project_name}', 'success')
    else:
        flash('No project name provided', 'error')
    return redirect(url_for('index'))

@app.route('/add-project', methods=['POST'])
def add_project():
    """Add a new project to the available list"""
    from flask import session
    
    project_name = request.form.get('new_project_name')
    if project_name:
        # Add to known projects
        if 'known_projects' not in session:
            session['known_projects'] = []
        if project_name not in session['known_projects']:
            session['known_projects'].append(project_name)
        
        # Switch to the new project
        set_current_project(project_name)
        flash(f'Added and switched to project: {project_name}', 'success')
    else:
        flash('No project name provided', 'error')
    return redirect(url_for('index'))

@app.route('/refresh-projects', methods=['POST'])
def refresh_projects():
    """Refresh/scan for available projects"""
    from flask import session
    
    # Clear cached projects to force a rescan
    if 'known_projects' in session:
        del session['known_projects']
    
    # Force a new scan by calling get_available_projects
    projects = get_available_projects()
    
    flash(f'Refreshed project list - found {len(projects)} projects', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
