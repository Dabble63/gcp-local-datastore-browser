#!/bin/bash

# Local Datastore Browser Startup Script

echo "🚀 Starting Local Datastore Browser..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

# Check if gcloud is available
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK is not installed."
    echo "   Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set up virtual environment
setup_venv() {
    VENV_DIR="venv"
    
    if [ -d "$VENV_DIR" ]; then
        echo "📁 Virtual environment found at ./$VENV_DIR"
    else
        echo "🆕 Creating virtual environment..."
        python3 -m venv $VENV_DIR
        if [ $? -ne 0 ]; then
            echo "❌ Failed to create virtual environment."
            exit 1
        fi
        echo "✅ Virtual environment created at ./$VENV_DIR"
    fi
    
    # Activate virtual environment
    echo "🔧 Activating virtual environment..."
    source $VENV_DIR/bin/activate
    if [ $? -ne 0 ]; then
        echo "❌ Failed to activate virtual environment."
        exit 1
    fi
    echo "✅ Virtual environment activated"
    
    # Upgrade pip to latest version
    echo "⬆️  Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    
    echo ""
}

# Install dependencies if requirements.txt exists
install_dependencies() {
    if [ -f "requirements.txt" ]; then
        echo "📦 Installing Python dependencies in virtual environment..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install dependencies. Please check the error above."
            exit 1
        fi
        echo "✅ Dependencies installed successfully!"
        echo ""
    fi
}

# Set up virtual environment
setup_venv

# Install dependencies
install_dependencies

# Check if datastore emulator is available
echo "🔍 Checking Google Cloud Datastore Emulator..."
if ! gcloud components list --filter="id:cloud-datastore-emulator" --format="value(state.name)" | grep -q "Installed"; then
    echo "❌ Datastore emulator is not installed."
    echo "   Installing now..."
    gcloud components install cloud-datastore-emulator
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install datastore emulator."
        exit 1
    fi
fi

echo "✅ Datastore emulator is available!"
echo ""

# Create data directory for emulator
mkdir -p ./datastore-data

# Function to start datastore emulator
start_emulator() {
    echo "🔧 Starting Google Cloud Datastore Emulator..."
    gcloud beta emulators datastore start --data-dir=./datastore-data --host-port=localhost:8081 &
    EMULATOR_PID=$!
    
    # Wait for emulator to start
    echo "⏳ Waiting for emulator to start..."
    sleep 5
    
    # Check if emulator is running
    if ! curl -s http://localhost:8081 > /dev/null 2>&1; then
        echo "❌ Failed to start datastore emulator on port 8081."
        echo "   Please check if port 8081 is available."
        exit 1
    fi
    
    echo "✅ Datastore emulator started on localhost:8081"
}

# Function to set environment variables
set_env_vars() {
    echo "🔧 Setting environment variables..."
    export DATASTORE_EMULATOR_HOST=localhost:8081
    export GOOGLE_CLOUD_PROJECT=mephysio-hrd-local
    echo "✅ Environment variables set"
    echo "   DATASTORE_EMULATOR_HOST=localhost:8081"
    echo "   GOOGLE_CLOUD_PROJECT=mephysio-hrd-local"
    echo ""
}

# Function to start Flask app
start_flask() {
    echo "🌐 Starting Flask application..."
    # Make sure we're using the virtual environment's Python
    ./venv/bin/python app.py &
    FLASK_PID=$!
    
    # Wait for Flask to start
    sleep 3
    
    # Check if Flask is running
    if ! curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "❌ Failed to start Flask application on port 5000."
        exit 1
    fi
    
    echo "✅ Flask application started on http://localhost:5000"
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null
        echo "✅ Flask application stopped"
    fi
    
    if [ ! -z "$EMULATOR_PID" ]; then
        kill $EMULATOR_PID 2>/dev/null
        echo "✅ Datastore emulator stopped"
    fi
    
    echo "👋 Goodbye!"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Main execution
echo "📋 Setup Summary:"
echo "   • Datastore Emulator: localhost:8081"
echo "   • Flask Application: localhost:5000"
echo "   • Data Directory: ./datastore-data"
echo ""

# Check if we should start emulator
read -p "🤔 Do you want to start the datastore emulator? (y/N): " start_emu
if [[ $start_emu =~ ^[Yy]$ ]]; then
    start_emulator
    set_env_vars
else
    echo "⚠️  Assuming datastore emulator is already running on localhost:8081"
    set_env_vars
fi

# Start Flask application
start_flask

echo ""
echo "🎉 Local Datastore Browser is now running!"
echo ""
echo "📱 Open your browser and navigate to:"
echo "   🔗 http://localhost:5000"
echo ""
echo "💡 Tips:"
echo "   • The datastore emulator stores data in ./datastore-data/"
echo "   • Python dependencies are isolated in ./venv/"
echo "   • Press Ctrl+C to stop all services"
echo "   • Check the terminal for any error messages"
echo ""
echo "⏳ Keeping services running... Press Ctrl+C to stop."

# Keep script running
while true; do
    sleep 1
done
