#!/bin/bash

# Script to help fix Docker Desktop WSL 2 integration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header "Docker Desktop WSL 2 Integration Setup"

# Check if running in WSL
if [ ! -f /proc/sys/fs/binfmt_misc/WSLInterop ]; then
    print_error "This script must be run inside WSL 2"
    exit 1
fi

print_info "Checking Docker installation status..."

# Option 1: Check if Docker is available through Windows
if command -v docker.exe &> /dev/null; then
    print_success "Docker Desktop is installed on Windows"
    print_info "You can use docker.exe and docker-compose.exe commands"
    
    print_header "Creating aliases for easier usage"
    
    # Add aliases to bashrc
    if ! grep -q "alias docker='docker.exe'" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Docker Desktop aliases" >> ~/.bashrc
        echo "alias docker='docker.exe'" >> ~/.bashrc
        echo "alias docker-compose='docker-compose.exe'" >> ~/.bashrc
        print_success "Aliases added to ~/.bashrc"
    else
        print_info "Aliases already exist in ~/.bashrc"
    fi
    
    print_header "Quick Fix Instructions"
    echo "1. Run this command to apply aliases immediately:"
    echo -e "   ${YELLOW}source ~/.bashrc${NC}"
    echo ""
    echo "2. Or better: Enable WSL integration in Docker Desktop:"
    echo "   - Open Docker Desktop on Windows"
    echo "   - Go to Settings → Resources → WSL Integration"
    echo "   - Enable integration with your distro"
    echo "   - Click 'Apply & Restart'"
    echo ""
    echo "3. After enabling WSL integration, restart your WSL terminal"
    
else
    print_error "Docker Desktop not detected"
    
    print_header "Installation Instructions"
    echo "1. Install Docker Desktop on Windows (not in WSL):"
    echo "   https://www.docker.com/products/docker-desktop/"
    echo ""
    echo "2. During installation, ensure 'Use WSL 2 based engine' is checked"
    echo ""
    echo "3. After installation:"
    echo "   - Open Docker Desktop"
    echo "   - Go to Settings → Resources → WSL Integration"
    echo "   - Enable integration with your WSL distro"
    echo "   - Apply & Restart"
    echo ""
    echo "4. Restart your WSL terminal and run setup_dev.sh again"
fi

# Alternative: Check if user wants to install Docker directly in WSL
print_header "Alternative: Install Docker in WSL (Not Recommended)"
print_warning "Installing Docker directly in WSL is not recommended"
print_info "Docker Desktop with WSL integration is the preferred method"

echo ""
read -p "Do you want to see instructions for native WSL Docker installation? (y/N): " install_native

if [[ "$install_native" =~ ^[Yy]$ ]]; then
    print_header "Native Docker Installation in WSL"
    echo "Run these commands to install Docker in WSL:"
    echo ""
    echo "# Update packages"
    echo "sudo apt update"
    echo ""
    echo "# Install dependencies"
    echo "sudo apt install -y apt-transport-https ca-certificates curl software-properties-common"
    echo ""
    echo "# Add Docker GPG key"
    echo "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -"
    echo ""
    echo "# Add Docker repository"
    echo "sudo add-apt-repository \"deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\""
    echo ""
    echo "# Install Docker"
    echo "sudo apt update"
    echo "sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin"
    echo ""
    echo "# Add user to docker group"
    echo "sudo usermod -aG docker $USER"
    echo ""
    echo "# Start Docker service"
    echo "sudo service docker start"
    echo ""
    print_warning "Note: You'll need to start Docker service manually each time WSL starts"
fi

print_header "Next Steps"
if command -v docker.exe &> /dev/null; then
    echo "1. Apply the aliases: source ~/.bashrc"
    echo "2. Or enable WSL integration in Docker Desktop (recommended)"
    echo "3. Run ./scripts/setup_dev.sh again"
else
    echo "1. Install Docker Desktop on Windows"
    echo "2. Enable WSL 2 integration"
    echo "3. Restart WSL terminal"
    echo "4. Run ./scripts/setup_dev.sh again"
fi