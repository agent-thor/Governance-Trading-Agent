#!/bin/bash
# Installation script for Governance Trading Bot

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[*] $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[!] $1${NC}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Ollama is installed
check_ollama() {
    if ! command_exists ollama; then
        print_error "Ollama is not installed. Please install it from https://ollama.com/download"
        exit 1
    fi
}

# Function to check if Python is installed
check_python() {
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
}

# Function to check if pip is installed
check_pip() {
    if ! command_exists pip3; then
        print_error "pip3 is not installed. Please install it first."
        exit 1
    fi
}

# Function to check if git is installed
check_git() {
    if ! command_exists git; then
        print_error "git is not installed. Please install it first."
        exit 1
    fi
}

# Function to check if required files exist
check_required_files() {
    if [ ! -f "exchange/coin.json" ]; then
        print_error "coin.json is missing in the exchange directory"
        exit 1
    fi
    
    if [ ! -f "exchange/precision.json" ]; then
        print_error "precision.json is missing in the exchange directory"
        exit 1
    fi
}

# Function to create data directory
create_data_dir() {
    if [ ! -d "data" ]; then
        print_status "Creating data directory..."
        mkdir -p data
    fi
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    pip3 install -r requirements.txt
}

# Function to download models
download_models() {
    print_status "Downloading trading models..."
    python3 download_models.py
}

# Function to create .env file
create_env_file() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from example..."
        cp .env.example .env
        print_warning "Please edit the .env file with your actual credentials"
    else
        print_warning ".env file already exists. Please make sure it's properly configured."
    fi
}

# Main installation process
main() {
    print_status "Starting installation of Governance Trading Agent..."
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    check_ollama
    check_python
    check_pip
    check_git
    
    # Check required files
    print_status "Checking required files..."
    check_required_files
    
    # Create data directory
    create_data_dir
    
    # Install dependencies
    install_dependencies
    
    # Download models
    download_models
    
    # Create .env file
    create_env_file
    
    print_status "Installation completed successfully!"
    print_warning "Please make sure to:"
    echo "1. Edit the .env file with your actual credentials"
    echo "2. Start Ollama in the background with: ollama serve"
    echo "3. Run the agent with: python -m main"
}

# Run the main function
main 