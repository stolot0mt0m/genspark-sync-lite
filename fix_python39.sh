#!/usr/bin/env bash
###############################################################################
# Quick Fix for Python 3.9 pip Issue
# 
# Description: Installs pip for existing Python 3.9 installation
# Usage: ./fix_python39.sh
###############################################################################

set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  GenSpark Sync Lite - Python 3.9 Pip Fix${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Python 3.9 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ python3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
echo ""

# Check if pip is already installed
if python3 -m pip --version &> /dev/null; then
    PIP_VERSION=$(python3 -m pip --version | awk '{print $2}')
    echo -e "${GREEN}✓ pip ${PIP_VERSION} already installed${NC}"
    echo ""
    echo -e "${BLUE}No fix needed! You can run:${NC}"
    echo -e "  ${GREEN}./install.sh${NC}"
    exit 0
fi

echo -e "${YELLOW}⚠ pip not found${NC}"
echo ""

# Method 1: Try ensurepip
echo -e "${BLUE}━━━ Method 1: Installing pip via ensurepip${NC}"
if python3 -m ensurepip --upgrade 2>/dev/null; then
    echo -e "${GREEN}✓ pip installed successfully${NC}"
    PIP_VERSION=$(python3 -m pip --version | awk '{print $2}')
    echo -e "${GREEN}✓ pip ${PIP_VERSION} ready${NC}"
    echo ""
    echo -e "${BLUE}Now you can run:${NC}"
    echo -e "  ${GREEN}./install.sh${NC}"
    exit 0
fi

# Method 2: Download get-pip.py
echo -e "${YELLOW}⚠ ensurepip failed, trying get-pip.py${NC}"
echo ""
echo -e "${BLUE}━━━ Method 2: Installing pip via get-pip.py${NC}"

# Download get-pip.py
echo "Downloading get-pip.py..."
if curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py; then
    echo -e "${GREEN}✓ Downloaded get-pip.py${NC}"
    
    # Install pip
    if python3 /tmp/get-pip.py --user; then
        echo -e "${GREEN}✓ pip installed successfully${NC}"
        
        # Clean up
        rm -f /tmp/get-pip.py
        
        PIP_VERSION=$(python3 -m pip --version | awk '{print $2}')
        echo -e "${GREEN}✓ pip ${PIP_VERSION} ready${NC}"
        echo ""
        echo -e "${BLUE}Now you can run:${NC}"
        echo -e "  ${GREEN}./install.sh${NC}"
        exit 0
    else
        echo -e "${RED}✗ Failed to install pip via get-pip.py${NC}"
        rm -f /tmp/get-pip.py
    fi
else
    echo -e "${RED}✗ Failed to download get-pip.py${NC}"
fi

# Method 3: Homebrew Python
echo ""
echo -e "${BLUE}━━━ Method 3: Install newer Python via Homebrew${NC}"
echo ""
echo -e "${YELLOW}Your Python 3.9 doesn't have pip.${NC}"
echo -e "${YELLOW}Recommended: Install Python 3.11 via Homebrew${NC}"
echo ""
read -p "Install Python 3.11 via Homebrew? [Y/n]: " -n 1 -r
echo

if [[ "${REPLY}" =~ ^[Yy]$|^$ ]]; then
    # Check Homebrew
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}✗ Homebrew not found${NC}"
        echo -e "${BLUE}Install Homebrew first:${NC}"
        echo -e "  ${GREEN}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
        exit 1
    fi
    
    # Install Python via Homebrew
    echo "Installing Python 3.11 via Homebrew..."
    if brew install python@3.11; then
        echo -e "${GREEN}✓ Python 3.11 installed${NC}"
        
        # Verify
        PYTHON3_11="/opt/homebrew/bin/python3.11"
        if [[ ! -f "${PYTHON3_11}" ]]; then
            PYTHON3_11="/usr/local/bin/python3.11"
        fi
        
        if [[ -f "${PYTHON3_11}" ]]; then
            NEW_VERSION=$("${PYTHON3_11}" --version 2>&1 | awk '{print $2}')
            PIP_VERSION=$("${PYTHON3_11}" -m pip --version | awk '{print $2}')
            echo -e "${GREEN}✓ Python ${NEW_VERSION} with pip ${PIP_VERSION}${NC}"
            echo ""
            echo -e "${BLUE}Now you can run:${NC}"
            echo -e "  ${GREEN}./install.sh${NC}"
            exit 0
        fi
    else
        echo -e "${RED}✗ Failed to install Python via Homebrew${NC}"
    fi
fi

# All methods failed
echo ""
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}  Failed to fix pip issue${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Manual steps:${NC}"
echo ""
echo "1. Install Homebrew (if not installed):"
echo -e "   ${BLUE}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
echo ""
echo "2. Install Python 3.11:"
echo -e "   ${BLUE}brew install python@3.11${NC}"
echo ""
echo "3. Run install script:"
echo -e "   ${BLUE}./install.sh${NC}"
echo ""

exit 1
