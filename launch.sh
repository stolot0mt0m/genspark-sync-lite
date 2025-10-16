#!/usr/bin/env bash
#
# GenSpark Sync Lite - Application Launcher
# Activates virtual environment and starts the sync app
#

set -euo pipefail

# Get script directory (works even if launched via symlink)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment
if [[ ! -f "$SCRIPT_DIR/venv/bin/activate" ]]; then
    echo "❌ Error: Virtual environment not found!"
    echo "   Run ./install.sh first to set up the environment."
    exit 1
fi

echo "🚀 Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

# Change to project directory
cd "$SCRIPT_DIR"

# Create sync folder if it doesn't exist
SYNC_FOLDER="${HOME}/GenSpark AI Drive"
if [[ ! -d "$SYNC_FOLDER" ]]; then
    echo "📁 Creating sync folder: $SYNC_FOLDER"
    mkdir -p "$SYNC_FOLDER"
fi

# Start the sync app
echo "🔄 Starting GenSpark Sync Lite..."
echo "   Sync Folder: $SYNC_FOLDER"
echo "   Press Ctrl+C to stop"
echo ""

# Pass all arguments to the Python script
exec python3 src/sync_app.py "$@"
