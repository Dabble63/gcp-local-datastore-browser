# Local Datastore Browser

A Python Flask-based GUI for browsing and editing Google Cloud Datastore entities running on the local Google Cloud Datastore emulator.

## Features

- 🔍 **Browse Entities**: View all entity kinds/tables in your local datastore
- 📊 **Paginated Views**: Handle large datasets with pagination
- ✏️ **Edit Entities**: Modify entity properties with validation
- ➕ **Create Entities**: Add new entities with custom properties
- 🗑️ **Delete Entities**: Remove entities with confirmation
- 🎨 **Modern UI**: Clean, responsive Bootstrap interface
- 🔧 **JSON Support**: Handle complex data types (objects, arrays)
- 🚀 **Easy Setup**: Simple configuration for local development

## Prerequisites

1. **Google Cloud SDK** installed
2. **Python 3.7+**
3. **Google Cloud Datastore Emulator**

## Installation

1. **Clone or download** this project to your local machine

2. **Run the startup script** (recommended):
   ```bash
   ./start.sh
   ```
   This will automatically:
   - Create a virtual environment if it doesn't exist
   - Activate the virtual environment
   - Install Python dependencies
   - Start the datastore emulator and Flask app

3. **Or install manually**:
   ```bash
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env if you need to change default settings
   ```

## Setup Google Cloud Datastore Emulator

1. **Install the emulator** (if not already installed):
   ```bash
   gcloud components install cloud-datastore-emulator
   ```

2. **Start the emulator**:
   ```bash
   gcloud beta emulators datastore start --data-dir=./datastore-data --host-port=localhost:8081
   ```

   This will:
   - Start the emulator on `localhost:8081`
   - Store data in `./datastore-data` directory
   - Keep data persistent between restarts

3. **Set environment variables** (in a new terminal):
   ```bash
   $(gcloud beta emulators datastore env-init)
   ```

## Running the Application

1. **Using the startup script** (recommended):
   ```bash
   ./start.sh
   ```
   This will handle everything: virtual environment setup, dependencies, emulator startup, and Flask app.

2. **Or start manually**:
   ```bash
   # Activate virtual environment
   source venv/bin/activate
   
   # Start datastore emulator (in one terminal)
   gcloud beta emulators datastore start --data-dir=./datastore-data --host-port=localhost:8081
   
   # Start Flask app (in another terminal)
   export DATASTORE_EMULATOR_HOST=localhost:8081
   export GOOGLE_CLOUD_PROJECT=test-project
   python app.py
   ```

3. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Browsing Entities

1. **Home Page**: Shows all available entity kinds/tables
2. **Kind Browser**: Click on any kind to view its entities
3. **Pagination**: Use the pagination controls to navigate large datasets
4. **Search**: Browse through entities with built-in pagination

### Creating Entities

1. **Navigate** to a kind or create a new one
2. **Click "New Entity"** button
3. **Add properties** using the dynamic form
4. **Specify entity ID** (optional - will auto-generate if empty)
5. **Use JSON format** for complex data types

### Editing Entities

1. **Click the edit button** (pencil icon) on any entity
2. **Modify properties** in the form
3. **Add or remove properties** as needed
4. **Save changes** or cancel

### Data Types

The browser supports all standard Datastore data types:

- **Strings**: Plain text values
- **Numbers**: Integers and floats (123, 45.67)
- **Booleans**: true or false
- **Arrays**: JSON arrays [1, 2, 3] or ["a", "b", "c"]
- **Objects**: JSON objects {"key": "value", "nested": {"data": 123}}
- **Null**: null values

### JSON Format Examples

**String**:
```
Hello World
```

**Number**:
```
42
3.14159
```

**Boolean**:
```
true
false
```

**Array**:
```json
[1, 2, 3, 4, 5]
["apple", "banana", "cherry"]
[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
```

**Object**:
```json
{
  "name": "John Doe",
  "age": 30,
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "zipcode": "12345"
  },
  "hobbies": ["reading", "swimming", "coding"]
}
```

## Configuration

The application can be configured via environment variables in the `.env` file:

```bash
# Datastore emulator settings
DATASTORE_EMULATOR_HOST=localhost:8081
GOOGLE_CLOUD_PROJECT=test-project

# Flask settings
FLASK_ENV=development
FLASK_DEBUG=True
```

## Project Structure

```
local_datastore_browser/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── README.md             # This file
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── browse_kind.html  # Entity listing
    ├── view_entity.html  # Entity details
    ├── edit_entity.html  # Entity editor
    └── new_entity.html   # Entity creator
```

## Troubleshooting

### Connection Issues

If you can't connect to the datastore:

1. **Check emulator status**:
   ```bash
   gcloud beta emulators datastore start --data-dir=./datastore-data
   ```

2. **Verify environment variables**:
   ```bash
   echo $DATASTORE_EMULATOR_HOST
   echo $GOOGLE_CLOUD_PROJECT
   ```

3. **Check the port**: Make sure port 8081 is not in use by another process

### No Entities Showing

If no entities appear:

1. **Create test data** using the Google Cloud SDK:
   ```bash
   # Set environment for emulator
   $(gcloud beta emulators datastore env-init)
   
   # Use gcloud or your application to create test entities
   ```

2. **Check project ID**: Ensure `GOOGLE_CLOUD_PROJECT` matches your emulator setup

### Import Errors

If you get import errors:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Check Python version**: Ensure you're using Python 3.7+

## API Endpoints

The application also provides a simple REST API:

- `GET /api/kinds` - Returns list of all entity kinds

## Development

To contribute or modify the application:

1. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Enable debug mode** in `.env`:
   ```bash
   FLASK_DEBUG=True
   ```

3. **Modify templates** in the `templates/` directory
4. **Update routes** in `app.py`

## Security Note

This application is designed for **local development only**. Do not use in production without proper authentication and security measures.

## License

This project is provided as-is for educational and development purposes.
