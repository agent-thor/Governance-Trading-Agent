#!/bin/bash
# Installation script for Governance Trading Bot

# Set up virtual environment
echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Update pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies using requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Install the package in development mode for console scripts
echo "Installing package in development mode..."
pip install -e .

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating sample .env file..."
    if [ -f "proposal_revamp/.env.example" ]; then
        cp proposal_revamp/.env.example .env
    else
        echo "Warning: .env.example not found. Creating a basic .env file."
        echo "DATA_DIR=./data" > .env
    fi
    echo "Please edit the .env file with your actual credentials."
fi

# Check if coin.json and precision.json files exist in root
if [ ! -f "coin.json" ]; then
    echo "Copying coin.json to root directory..."
    cp proposal_revamp/exchange/coin.json ./coin.json
fi

if [ ! -f "precision.json" ]; then
    echo "Copying precision.json to root directory..."
    cp proposal_revamp/exchange/precision.json ./precision.json
fi

# Create data directory if not exists
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Create trained_model directories
if [ ! -d "trained_model" ]; then
    echo "Creating trained_model directories..."
    mkdir -p trained_model/bullish trained_model/bearish trained_model/sentiment
    
    echo ""
    echo "Downloading trading models..."
    cd proposal_revamp1 && python download_models.py && cd ..
    
    # Check if the download was successful
    if [ $? -ne 0 ]; then
        echo ""
        echo "IMPORTANT: Automatic download failed. You need to download the trading models manually."
        echo "Please download from: https://drive.google.com/file/d/1zjDwBqagqUPZ8H-igv4KlxdyFA8S4pe3/view?usp=sharing"
        echo "After downloading, extract the files to the respective directories:"
        echo "  - trained_model/bullish/"
        echo "  - trained_model/bearish/"
        echo "  - trained_model/sentiment/"
        echo ""
        echo "Or follow the instructions in the README.md file."
    fi
fi

# Check if Ollama is installed
echo "Checking for Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install it manually for text summarization."
    echo "For macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "For Windows: Download from https://ollama.com/download"
    echo "Then run: ollama pull mistral:7b"
else
    echo "Ollama is installed. Checking for mistral:7b model..."
    if ! ollama list | grep -q "mistral:7b"; then
        echo "Downloading mistral:7b model for Ollama..."
        ollama pull mistral:7b
    else
        echo "Mistral:7b model is already installed."
    fi
fi

echo ""
echo "Installation complete!"
echo "To activate the environment: source venv/bin/activate"
echo "To run the bot: python main.py"
echo "Or use the console entry point: governance-bot"
echo "" 