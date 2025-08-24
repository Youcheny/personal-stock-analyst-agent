#!/bin/bash
# Convenience script to run the value-agent-adk application
# Usage: ./run.sh memo AAPL
# Usage: ./run.sh screen --universe AAPL,MSFT,META

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Run the app with all arguments passed to this script
python3 src/app.py "$@"
