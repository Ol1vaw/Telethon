#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
PYTHON_SCRIPT="$SCRIPT_DIR/rental_filter.py"
SESSION_FILE="$SCRIPT_DIR/rental_filter.session"
STATE_FILE="$SCRIPT_DIR/rental_filter_state.pkl"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Start the Python script with nohup and redirect all output to a log file
# The log file name includes the date when the script was started
LOG_FILE="$LOG_DIR/rental_filter_$(date +%Y%m%d_%H%M%S).log"

echo "Starting rental filter script..."
echo "Logs will be written to: $LOG_FILE"

# Make sure the Python script is executable
chmod +x "$PYTHON_SCRIPT"

# Kill any existing instances of the script
pkill -f "$PYTHON_SCRIPT" || true
sleep 1
# Use a stronger kill command if processes are still running
pkill -9 -f "$PYTHON_SCRIPT" || true
echo "Killed any existing instances of the script"

# Wait a moment for processes to terminate
sleep 2

# Remove any existing session files to prevent database lock issues
rm -f "${SESSION_FILE}"* "${STATE_FILE}"
echo "Removed any existing session files"

# Make sure the environment variables are set
# Don't use the local Telethon library
unset PYTHONPATH
export PYTHONUNBUFFERED=1

# Start the script with nohup
nohup python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &

# Save the PID to a file for later management
echo $! > "$LOG_DIR/rental_filter.pid"

echo "Rental filter script started with PID: $!"
echo "To view logs in real-time, use: tail -f $LOG_FILE"
echo "To stop the script, use: kill $(cat "$LOG_DIR/rental_filter.pid")" 