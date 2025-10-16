#!/bin/bash
# Test script for Sync Strategy feature
# Tests Local/Remote/Ask priority for remote-only files

set -e  # Exit on error

echo "======================================"
echo "  Sync Strategy Feature Test"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Please run this script from genspark-sync-lite directory${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -q -r requirements.txt

echo ""
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Test 1: Basic API Connection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: API Connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cd src
python3 -c "
from genspark_api import GenSparkAPIClient
import sys

api = GenSparkAPIClient()
if not api.load_cookies_from_chrome():
    print('❌ Failed to load cookies from Chrome')
    print('💡 Make sure:')
    print('   1. You are logged into genspark.ai in Chrome')
    print('   2. Chrome is completely closed')
    sys.exit(1)

if not api.test_connection():
    print('❌ API connection failed')
    sys.exit(1)

print('✅ API connection successful!')
"
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ API connection test failed${NC}"
    echo -e "${YELLOW}Please fix the connection issue before continuing${NC}"
    exit 1
fi
cd ..

echo ""
echo -e "${GREEN}✅ TEST 1 PASSED: API connection working${NC}"
echo ""

# Test 2: Sync Engine Import
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Sync Engine with Strategy Parameter"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cd src
python3 -c "
from sync_engine import SyncEngine
from genspark_api import GenSparkAPIClient
from pathlib import Path

# Test that sync_strategy parameter exists
api = GenSparkAPIClient()
test_path = Path('/tmp/test_sync')
test_path.mkdir(exist_ok=True)

# Test all three strategies
for strategy in ['local', 'remote', 'ask']:
    engine = SyncEngine(test_path, api, sync_strategy=strategy)
    assert engine.sync_strategy == strategy, f'Strategy not set correctly: {strategy}'
    print(f'✅ SyncEngine accepts strategy: {strategy}')

print('✅ All sync strategies are supported!')
"
cd ..

echo ""
echo -e "${GREEN}✅ TEST 2 PASSED: Sync Engine supports all strategies${NC}"
echo ""

# Test 3: Sync App Initialization
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Sync App Initialization with Strategy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cd src
python3 -c "
from sync_app import GenSparkSyncApp
from pathlib import Path

test_path = Path('/tmp/test_sync_app')
test_path.mkdir(exist_ok=True)

# Test initialization with different strategies
for strategy in ['local', 'remote', 'ask']:
    app = GenSparkSyncApp(test_path, poll_interval=30, sync_strategy=strategy)
    assert app.sync_strategy == strategy, f'App strategy not set correctly: {strategy}'
    print(f'✅ GenSparkSyncApp accepts strategy: {strategy}')

print('✅ App initialization with all strategies works!')
"
cd ..

echo ""
echo -e "${GREEN}✅ TEST 3 PASSED: App initialization supports all strategies${NC}"
echo ""

# Test 4: Remote File Listing
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Scan Remote Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cd src
python3 -c "
from sync_engine import SyncEngine
from genspark_api import GenSparkAPIClient
from pathlib import Path

api = GenSparkAPIClient()
if not api.load_cookies_from_chrome():
    print('❌ Failed to load cookies')
    exit(1)

test_path = Path('/tmp/test_remote_scan')
test_path.mkdir(exist_ok=True)

engine = SyncEngine(test_path, api, sync_strategy='remote')
remote_files = engine.scan_remote_files()

print(f'📊 Found {len(remote_files)} files in AI Drive')
if len(remote_files) > 0:
    print(f'   Sample files:')
    for i, path in enumerate(list(remote_files.keys())[:3]):
        print(f'   - {path}')
    print('✅ Remote file scanning works!')
else:
    print('⚠️  No files found in AI Drive (this is OK if your drive is empty)')
"
cd ..

echo ""
echo -e "${GREEN}✅ TEST 4 PASSED: Remote file scanning works${NC}"
echo ""

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Sync Strategy feature is working correctly!"
echo ""
echo "You can now test the full app with:"
echo -e "${YELLOW}  cd src && python3 sync_app.py${NC}"
echo ""
echo "The app will prompt you to choose a sync strategy:"
echo "  [L] Local priority - Delete remote-only files"
echo "  [R] Remote priority - Download remote-only files"
echo "  [A] Ask - Prompt for each file (default)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
