#!/bin/bash
# Quick test script for GenSpark Sync Lite API

echo "======================================"
echo "  GenSpark Sync Lite - API Test"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from genspark-sync-lite directory"
    exit 1
fi

echo "📦 Installing dependencies..."
pip3 install -q -r requirements.txt

echo ""
echo "🔍 Testing API connection..."
echo ""

cd src
python3 genspark_api.py

echo ""
echo "======================================"
echo "If you see '✅ API connection successful!'"
echo "then you're ready to run the sync app!"
echo ""
echo "Start with: python3 src/sync_app.py"
echo "======================================"
