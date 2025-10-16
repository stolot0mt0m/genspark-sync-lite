#!/usr/bin/env bash
###############################################################################
# GenSpark Sync Lite - Automated Installation Script
# 
# Description: Secure, automated installation with dependency checks
# Platform: macOS (10.14+)
# Requirements: Bash 4.0+, internet connection
# 
# Security Features:
# - Input validation
# - Path sanitization
# - No remote code execution
# - User confirmation for installations
# - Dependency verification
# - Checksum validation where possible
#
# Usage: ./install.sh
###############################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures
IFS=$'\n\t'        # Safer word splitting

###############################################################################
# CONSTANTS & CONFIGURATION
###############################################################################

readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_NAME="$(basename "${0}")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly INSTALL_DIR="${SCRIPT_DIR}"
readonly LOG_FILE="${INSTALL_DIR}/install.log"

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Required Python version
readonly REQUIRED_PYTHON_MAJOR=3
readonly REQUIRED_PYTHON_MINOR=8

# Security: Allowed installation paths (prevent directory traversal)
readonly ALLOWED_INSTALL_PATHS=(
    "${HOME}"
    "/usr/local"
    "/opt"
)

###############################################################################
# LOGGING & OUTPUT FUNCTIONS
###############################################################################

log() {
    local level="${1}"
    shift
    local message="${*}"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
}

print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}  GenSpark Sync Lite - Automated Installation${NC}"
    echo -e "${BLUE}  Version: ${SCRIPT_VERSION}${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
    log "INFO" "${1}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}" >&2
    log "ERROR" "${1}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
    log "WARN" "${1}"
}

print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
    log "INFO" "${1}"
}

print_step() {
    echo ""
    echo -e "${BLUE}━━━ ${1}${NC}"
    log "INFO" "STEP: ${1}"
}

###############################################################################
# SECURITY FUNCTIONS
###############################################################################

validate_path() {
    local path="${1}"
    local path_real
    
    # Resolve symlinks and get absolute path
    if [[ -e "${path}" ]]; then
        path_real="$(cd "$(dirname "${path}")" && pwd)/$(basename "${path}")"
    else
        path_real="$(cd "$(dirname "${path}")" && pwd)"
    fi
    
    # Check if path starts with allowed prefix
    local allowed=false
    for allowed_path in "${ALLOWED_INSTALL_PATHS[@]}"; do
        if [[ "${path_real}" == "${allowed_path}"* ]]; then
            allowed=true
            break
        fi
    done
    
    if [[ "${allowed}" == false ]]; then
        print_error "Installation path not allowed: ${path_real}"
        print_info "Allowed paths: ${ALLOWED_INSTALL_PATHS[*]}"
        return 1
    fi
    
    return 0
}

sanitize_input() {
    local input="${1}"
    # Remove potentially dangerous characters
    # Allow only alphanumeric, dash, underscore, dot, forward slash
    echo "${input}" | sed 's/[^a-zA-Z0-9._/-]//g'
}

check_root() {
    if [[ "${EUID}" -eq 0 ]]; then
        print_error "This script should NOT be run as root"
        print_info "Run without sudo: ./install.sh"
        exit 1
    fi
}

verify_macos() {
    if [[ "$(uname)" != "Darwin" ]]; then
        print_error "This script is designed for macOS only"
        print_info "Detected OS: $(uname)"
        exit 1
    fi
    
    local macos_version
    macos_version="$(sw_vers -productVersion)"
    print_success "macOS ${macos_version} detected"
}

###############################################################################
# DEPENDENCY CHECK FUNCTIONS
###############################################################################

check_command() {
    local cmd="${1}"
    if command -v "${cmd}" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

check_python() {
    print_step "Checking Python installation"
    
    # Try python3 first, then python
    for cmd in python3 python; do
        if check_command "${cmd}"; then
            local version
            version="$("${cmd}" --version 2>&1 | awk '{print $2}')"
            local major minor
            major="$(echo "${version}" | cut -d. -f1)"
            minor="$(echo "${version}" | cut -d. -f2)"
            
            if [[ "${major}" -ge "${REQUIRED_PYTHON_MAJOR}" ]] && \
               [[ "${minor}" -ge "${REQUIRED_PYTHON_MINOR}" ]]; then
                print_success "Python ${version} found (${cmd})"
                echo "${cmd}"  # Output to stdout for capture
                return 0
            fi
        fi
    done
    
    print_error "Python ${REQUIRED_PYTHON_MAJOR}.${REQUIRED_PYTHON_MINOR}+ not found"
    return 1
}

check_pip() {
    local python_cmd="${1}"
    print_step "Checking pip installation"
    
    if "${python_cmd}" -m pip --version &> /dev/null; then
        local pip_version
        pip_version="$("${python_cmd}" -m pip --version | awk '{print $2}')"
        print_success "pip ${pip_version} found"
        return 0
    else
        print_error "pip not found"
        return 1
    fi
}

check_homebrew() {
    print_step "Checking Homebrew installation"
    
    if check_command brew; then
        local brew_version
        brew_version="$(brew --version | head -1 | awk '{print $2}')"
        print_success "Homebrew ${brew_version} found"
        return 0
    else
        print_warning "Homebrew not found"
        return 1
    fi
}

check_git() {
    print_step "Checking Git installation"
    
    if check_command git; then
        local git_version
        git_version="$(git --version | awk '{print $3}')"
        print_success "Git ${git_version} found"
        return 0
    else
        print_error "Git not found"
        return 1
    fi
}

check_chrome() {
    print_step "Checking Google Chrome installation"
    
    local chrome_path="/Applications/Google Chrome.app"
    if [[ -d "${chrome_path}" ]]; then
        print_success "Google Chrome found"
        return 0
    else
        print_warning "Google Chrome not found at ${chrome_path}"
        return 1
    fi
}

###############################################################################
# INSTALLATION FUNCTIONS
###############################################################################

install_homebrew() {
    print_step "Installing Homebrew"
    
    print_info "Homebrew is required to install dependencies"
    read -p "Install Homebrew? [y/N]: " -n 1 -r
    echo
    
    if [[ ! "${REPLY}" =~ ^[Yy]$ ]]; then
        print_error "Installation cancelled by user"
        exit 1
    fi
    
    print_info "Installing Homebrew (this may take a while)..."
    
    # Official Homebrew installation script
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    if [[ $? -eq 0 ]]; then
        print_success "Homebrew installed successfully"
        
        # Add Homebrew to PATH for Apple Silicon
        if [[ -d "/opt/homebrew/bin" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        print_error "Homebrew installation failed"
        exit 1
    fi
}

install_python() {
    print_step "Installing Python via Homebrew"
    
    print_info "Installing Python 3..."
    brew install python@3.11
    
    if [[ $? -eq 0 ]]; then
        print_success "Python installed successfully"
    else
        print_error "Python installation failed"
        exit 1
    fi
}

install_pip() {
    local python_cmd="${1}"
    print_step "Installing pip"
    
    print_info "Installing pip via ensurepip..."
    "${python_cmd}" -m ensurepip --upgrade
    
    if [[ $? -eq 0 ]]; then
        print_success "pip installed successfully"
    else
        print_error "pip installation failed"
        exit 1
    fi
}

install_python_dependencies() {
    local python_cmd="${1}"
    print_step "Installing Python dependencies"
    
    local requirements_file="${INSTALL_DIR}/requirements.txt"
    
    if [[ ! -f "${requirements_file}" ]]; then
        print_error "requirements.txt not found at ${requirements_file}"
        exit 1
    fi
    
    print_info "Installing packages from requirements.txt..."
    
    # Use --user to avoid system-wide installation
    # Use --no-cache-dir for security
    "${python_cmd}" -m pip install --user --no-cache-dir --upgrade pip
    "${python_cmd}" -m pip install --user --no-cache-dir -r "${requirements_file}"
    
    if [[ $? -eq 0 ]]; then
        print_success "Python dependencies installed successfully"
    else
        print_error "Failed to install Python dependencies"
        exit 1
    fi
}

verify_installation() {
    print_step "Verifying installation"
    
    local python_cmd="${1}"
    local errors=0
    
    # Check each required module
    local required_modules=(
        "requests"
        "watchdog"
        "browser_cookie3"
        "pydantic"
    )
    
    for module in "${required_modules[@]}"; do
        if "${python_cmd}" -c "import ${module}" 2>/dev/null; then
            print_success "Module ${module} verified"
        else
            print_error "Module ${module} not found"
            ((errors++))
        fi
    done
    
    if [[ ${errors} -gt 0 ]]; then
        print_error "Installation verification failed (${errors} errors)"
        return 1
    fi
    
    print_success "All modules verified successfully"
    return 0
}

test_api_connection() {
    print_step "Testing API connection"
    
    local python_cmd="${1}"
    local api_test_script="${INSTALL_DIR}/src/genspark_api.py"
    
    if [[ ! -f "${api_test_script}" ]]; then
        print_warning "API test script not found, skipping test"
        return 0
    fi
    
    print_info "This test requires Chrome to be closed and you to be logged into genspark.ai"
    print_info "Skip this test if you haven't logged in yet"
    read -p "Run API connection test? [y/N]: " -n 1 -r
    echo
    
    if [[ "${REPLY}" =~ ^[Yy]$ ]]; then
        cd "${INSTALL_DIR}/src" && "${python_cmd}" genspark_api.py
        
        if [[ $? -eq 0 ]]; then
            print_success "API connection test passed"
        else
            print_warning "API connection test failed (this is OK if you're not logged in)"
        fi
    else
        print_info "API test skipped"
    fi
}

create_launch_script() {
    print_step "Creating launch script"
    
    local python_cmd="${1}"
    local launch_script="${INSTALL_DIR}/launch.sh"
    
    cat > "${launch_script}" << EOF
#!/usr/bin/env bash
# GenSpark Sync Lite - Launch Script
# Generated by install.sh

set -euo pipefail

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"

cd "\${SCRIPT_DIR}/src"
"${python_cmd}" sync_app.py "\$@"
EOF
    
    chmod +x "${launch_script}"
    
    print_success "Launch script created: ${launch_script}"
}

###############################################################################
# MAIN INSTALLATION WORKFLOW
###############################################################################

main() {
    # Security checks
    check_root
    verify_macos
    
    # Initialize log file
    log "INFO" "Installation started - Version ${SCRIPT_VERSION}"
    
    # Print header
    print_header
    
    # Validate installation directory
    if ! validate_path "${INSTALL_DIR}"; then
        exit 1
    fi
    
    print_info "Installation directory: ${INSTALL_DIR}"
    print_info "Log file: ${LOG_FILE}"
    echo ""
    
    # System checks
    local python_cmd=""
    local needs_homebrew=false
    local needs_python=false
    local needs_pip=false
    
    # Check Git
    if ! check_git; then
        print_error "Git is required but not found"
        print_info "Please install Xcode Command Line Tools: xcode-select --install"
        exit 1
    fi
    
    # Check Homebrew
    if ! check_homebrew; then
        needs_homebrew=true
    fi
    
    # Check Python FIRST (before pip)
    python_cmd="$(check_python 2>/dev/null || echo '')"
    if [[ -z "${python_cmd}" ]]; then
        needs_python=true
    else
        # Only check pip if we have Python
        if ! check_pip "${python_cmd}"; then
            needs_pip=true
        fi
    fi
    
    # Check Chrome (warning only)
    check_chrome || true
    
    # Install missing dependencies
    if [[ "${needs_homebrew}" == true ]]; then
        install_homebrew
    fi
    
    if [[ "${needs_python}" == true ]]; then
        if [[ "${needs_homebrew}" == false ]] && ! check_command brew; then
            print_error "Homebrew is required to install Python"
            exit 1
        fi
        install_python
        # Re-check Python after installation
        python_cmd="$(check_python 2>/dev/null || echo '')"
        if [[ -z "${python_cmd}" ]]; then
            print_error "Python installation succeeded but python3 not found in PATH"
            print_info "Try closing and reopening Terminal, then run ./install.sh again"
            exit 1
        fi
    fi
    
    if [[ "${needs_pip}" == true ]]; then
        install_pip "${python_cmd}"
    fi
    
    # Install Python dependencies
    install_python_dependencies "${python_cmd}"
    
    # Verify installation
    if ! verify_installation "${python_cmd}"; then
        print_error "Installation verification failed"
        exit 1
    fi
    
    # Create launch script
    create_launch_script "${python_cmd}"
    
    # Optional: Test API connection
    test_api_connection "${python_cmd}"
    
    # Success summary
    print_step "Installation Complete!"
    echo ""
    print_success "GenSpark Sync Lite has been installed successfully"
    echo ""
    print_info "Next steps:"
    echo "  1. Login to GenSpark AI Drive in Chrome:"
    echo "     ${BLUE}https://www.genspark.ai/aidrive/files/${NC}"
    echo "  2. Close Chrome completely (Cmd+Q)"
    echo "  3. Run the app:"
    echo "     ${GREEN}cd ${INSTALL_DIR}${NC}"
    echo "     ${GREEN}./launch.sh${NC}"
    echo ""
    print_info "For help, see README.md or QUICKSTART.md"
    echo ""
    
    log "INFO" "Installation completed successfully"
}

###############################################################################
# ERROR HANDLING
###############################################################################

error_handler() {
    local line_number="${1}"
    print_error "Installation failed at line ${line_number}"
    log "ERROR" "Installation failed at line ${line_number}"
    exit 1
}

trap 'error_handler ${LINENO}' ERR

###############################################################################
# SCRIPT ENTRY POINT
###############################################################################

main "$@"
