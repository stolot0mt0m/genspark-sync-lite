#!/usr/bin/env bash
###############################################################################
# Debug Installation Issues
###############################################################################

set -euo pipefail

echo "=========================================="
echo "  GenSpark Sync Lite - Installation Debug"
echo "=========================================="
echo ""

echo "1. Python Check:"
echo "   which python3: $(which python3 || echo 'NOT FOUND')"
echo "   python3 --version: $(python3 --version 2>&1 || echo 'ERROR')"
echo ""

echo "2. Pip Check:"
echo "   which pip3: $(which pip3 || echo 'NOT FOUND')"
echo "   pip3 --version: $(pip3 --version 2>&1 || echo 'ERROR')"
echo ""

echo "3. Python -m pip Check:"
echo "   python3 -m pip --version: $(python3 -m pip --version 2>&1 || echo 'ERROR')"
echo ""

echo "4. PATH:"
echo "   $PATH"
echo ""

echo "5. Python sys.path:"
python3 -c "import sys; print('   ' + '\n   '.join(sys.path))" 2>&1 || echo "   ERROR"
echo ""

echo "6. Pip installation location:"
python3 -m pip show pip 2>/dev/null | grep Location || echo "   pip not found via python3 -m pip"
echo ""

echo "7. User site-packages:"
python3 -c "import site; print('   ' + site.USER_SITE)" 2>&1 || echo "   ERROR"
echo ""

echo "8. Test import:"
echo "   requests: $(python3 -c 'import requests; print(requests.__version__)' 2>&1 || echo 'NOT INSTALLED')"
echo "   watchdog: $(python3 -c 'import watchdog; print(watchdog.__version__)' 2>&1 || echo 'NOT INSTALLED')"
echo "   browser_cookie3: $(python3 -c 'import browser_cookie3; print(browser_cookie3.__version__)' 2>&1 || echo 'NOT INSTALLED')"
echo "   pydantic: $(python3 -c 'import pydantic; print(pydantic.__version__)' 2>&1 || echo 'NOT INSTALLED')"
echo ""

echo "=========================================="
echo ""
echo "If 'python3 -m pip --version' works but script fails,"
echo "the issue is with how the script captures the python command."
echo ""
echo "Try running install manually:"
echo "  python3 -m pip install --user -r requirements.txt"
echo ""
