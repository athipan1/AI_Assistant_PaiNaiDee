#!/bin/bash

# PaiNaiDee AI Assistant - Complete Setup Script
# This script sets up both the backend and mobile app

echo "🚀 Setting up PaiNaiDee AI Assistant..."
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check dependencies
check_dependencies() {
    print_header "📋 Checking Dependencies..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.8+ is required but not found"
        exit 1
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_status "Node.js $NODE_VERSION found"
    else
        print_error "Node.js 18+ is required but not found"
        exit 1
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_status "npm $NPM_VERSION found"
    else
        print_error "npm is required but not found"
        exit 1
    fi
}

# Setup backend
setup_backend() {
    print_header "🐍 Setting up Backend (Python FastAPI)..."
    
    cd painaidee_ai_assistant
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate || {
        print_warning "Failed to activate venv, trying without virtual environment..."
    }
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    cd ..
}

# Setup mobile app
setup_mobile() {
    print_header "📱 Setting up Mobile App (React Native + Expo)..."
    
    cd mobile-app
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install --legacy-peer-deps
    
    # Install additional web dependencies
    print_status "Installing web support dependencies..."
    npm install react-dom react-native-web @expo/metro-runtime --legacy-peer-deps
    
    cd ..
}

# Get local IP address
get_local_ip() {
    if command -v ip &> /dev/null; then
        LOCAL_IP=$(ip route get 1 | sed -n 's/^.*src \([0-9.]*\) .*$/\1/p')
    elif command -v ifconfig &> /dev/null; then
        LOCAL_IP=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    else
        LOCAL_IP="localhost"
    fi
    echo $LOCAL_IP
}

# Configure mobile app
configure_mobile() {
    print_header "⚙️  Configuring Mobile App..."
    
    LOCAL_IP=$(get_local_ip)
    print_status "Detected local IP: $LOCAL_IP"
    
    # Update config file
    CONFIG_FILE="mobile-app/src/config/index.ts"
    if [ -f "$CONFIG_FILE" ]; then
        sed -i.bak "s/http:\/\/192\.168\.1\.100:8000/http:\/\/$LOCAL_IP:8000/g" "$CONFIG_FILE"
        print_status "Updated mobile app config to use $LOCAL_IP:8000"
    else
        print_warning "Config file not found: $CONFIG_FILE"
    fi
}

# Main setup function
main() {
    print_header "🎯 PaiNaiDee AI Assistant Setup"
    echo "This script will set up both the backend and mobile app."
    echo
    
    check_dependencies
    echo
    
    setup_backend
    echo
    
    setup_mobile
    echo
    
    configure_mobile
    echo
    
    print_header "✅ Setup Complete!"
    echo
    print_status "To start the system:"
    echo
    echo "1. Start the backend server:"
    echo "   cd painaidee_ai_assistant"
    echo "   python main.py"
    echo
    echo "2. In a new terminal, start the mobile app:"
    echo "   cd mobile-app"
    echo "   npm start"
    echo
    print_status "Backend will run on: http://$(get_local_ip):8000"
    print_status "Mobile app will run on: http://localhost:8081"
    echo
    print_warning "Make sure both your computer and mobile device are on the same WiFi network!"
    echo
    print_header "🎉 Happy coding!"
}

# Run main function
main "$@"