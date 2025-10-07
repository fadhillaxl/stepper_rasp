#!/bin/bash
# Open Ground Station Rotator Controller Startup Script
# This script starts the rotator controller with proper permissions and logging

echo "=========================================="
echo "Open Ground Station Rotator Controller"
echo "Starting OGRC main application..."
echo "=========================================="

# Check if running as root (required for GPIO access)
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root for GPIO access"
    echo "Please run: sudo ./start_rotator.sh"
    exit 1
fi

# Check if Python dependencies are installed
echo "Checking dependencies..."
python3 -c "import RPi.GPIO, serial, dotenv, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: Missing Python dependencies"
    echo "Please install system-wide: sudo pip3 install RPi.GPIO pyserial python-dotenv pyyaml"
    echo "Note: sudo is required because this script runs with root privileges for GPIO access"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please ensure .env file exists with GPIO pin configurations"
    exit 1
fi

# Check if motor_config.yaml exists
if [ ! -f "motor_config.yaml" ]; then
    echo "Warning: motor_config.yaml not found, using default configuration"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set up log rotation
LOG_FILE="logs/rotator_$(date +%Y%m%d_%H%M%S).log"

echo "Starting rotator controller..."
echo "Log file: $LOG_FILE"
echo "TCP Server will listen on port 4533"
echo "Press Ctrl+C to stop"
echo ""

# Start the main application
python3 main.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "Rotator controller stopped."