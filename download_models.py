#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to download trading models from Google Drive.
"""

import os
import sys
import subprocess
import platform
import tempfile
import shutil

def create_directories():
    """Create the necessary directories for the models."""
    os.makedirs('trained_model/bullish', exist_ok=True)
    os.makedirs('trained_model/bearish', exist_ok=True)
    os.makedirs('trained_model/sentiment', exist_ok=True)
    print("Created model directories.")

def check_requirements():
    """Check if the required tools are installed."""
    try:
        # Check if gdown is installed
        subprocess.run(['pip', 'show', 'gdown'], 
                      check=True, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Installing gdown...")
        subprocess.run(['pip', 'install', 'gdown'])
    
    # Check if unzip is installed (for Linux/MacOS)
    if platform.system() != "Windows":
        try:
            subprocess.run(['which', 'unzip'], 
                          check=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            print("Error: 'unzip' is not installed. Please install it.")
            if platform.system() == "Linux":
                print("You can install it with: sudo apt-get install unzip")
            elif platform.system() == "Darwin":  # MacOS
                print("You can install it with: brew install unzip")
            sys.exit(1)

def download_models():
    """Download the models from Google Drive."""
    print("Downloading trading models...")
    # Define the Google Drive file ID for the model zip file
    file_id = "1zjDwBqagqUPZ8H-igv4KlxdyFA8S4pe3"
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download the zip file
        try:
            zip_path = os.path.join(temp_dir, "trading_models.zip")
            subprocess.run(
                ['gdown', f'https://drive.google.com/uc?id={file_id}', 
                 '-O', zip_path],
                check=True
            )
            print("Models downloaded successfully.")
            
            # Extract the zip file
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            print("Extracting models...")
            if platform.system() == "Windows":
                # Use Python's zipfile for Windows
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                # Use unzip command for Linux/MacOS
                subprocess.run(['unzip', zip_path, '-d', extract_dir], check=True)
            
            # Copy the extracted files to the appropriate directories
            print("Copying model files to target directories...")
            
            # Find the base directory containing the model folders
            extract_base = extract_dir
            
            # Check each directory in the extracted folder to find the model directories
            # Specifically looking for the "trading_model_Dec 2" directory
            for item in os.listdir(extract_dir):
                if os.path.isdir(os.path.join(extract_dir, item)) and "trading_model" in item:
                    potential_base = os.path.join(extract_dir, item)
                    # Check if this directory contains our model folders
                    model_dirs_found = 0
                    for model_type in ['bullish', 'bearish', 'sentiment']:
                        if os.path.exists(os.path.join(potential_base, model_type)):
                            model_dirs_found += 1
                    
                    if model_dirs_found > 0:
                        extract_base = potential_base
                        print(f"Found model directory: {item}")
                        break
            
            print(f"Using base directory: {os.path.basename(extract_base)}")
            
            # Now copy the model directories
            for model_type in ['bullish', 'bearish', 'sentiment']:
                source_dir = os.path.join(extract_base, model_type)
                target_dir = os.path.join('trained_model', model_type)
                
                if os.path.exists(source_dir):
                    print(f"Copying {model_type} model files from {source_dir}...")
                    # Clear the target directory first to avoid mixing old and new files
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # List all files to copy for debugging
                    model_files = os.listdir(source_dir)
                    print(f"Found {len(model_files)} files in {model_type}: {', '.join(model_files)}")
                    
                    # Copy all files from source to target
                    for item in model_files:
                        s = os.path.join(source_dir, item)
                        d = os.path.join(target_dir, item)
                        if os.path.isdir(s):
                            print(f"Copying directory: {item}")
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            print(f"Copying file: {item}")
                            shutil.copy2(s, d)
                else:
                    print(f"Warning: Could not find {model_type} directory in {extract_base}")
            
            print("Model files copied successfully.")
            
            # Update .env file with correct paths if it exists
            update_env_file()
            
            return
        except subprocess.CalledProcessError as e:
            print(f"Error downloading models: {e}")
            print("Please download the models manually from the Google Drive link.")
            print("https://drive.google.com/file/d/1zjDwBqagqUPZ8H-igv4KlxdyFA8S4pe3/view?usp=sharing")

def update_env_file():
    """Update .env file with correct model paths."""
    env_file = '.env'
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    
    # If we're in the proposal_revamp directory, check for .env in parent dir
    if os.path.basename(os.getcwd()) == 'proposal_revamp1':
        env_path = os.path.join(parent_dir, env_file)
    else:
        env_path = env_file
    
    if os.path.exists(env_path):
        print(f"Updating model paths in {env_path}...")
        
        # Read existing .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add the model directory variables
        bullish_found = bearish_found = sentiment_found = False
        
        for i, line in enumerate(lines):
            if line.startswith('BULLISH_DIR='):
                lines[i] = f'BULLISH_DIR=./trained_model/bullish\n'
                bullish_found = True
            elif line.startswith('BEARISH_DIR='):
                lines[i] = f'BEARISH_DIR=./trained_model/bearish\n'
                bearish_found = True
            elif line.startswith('SENTIMENT_DIR='):
                lines[i] = f'SENTIMENT_DIR=./trained_model/sentiment\n'
                sentiment_found = True
        
        # If any variables weren't found, add them
        if not (bullish_found and bearish_found and sentiment_found):
            for i, line in enumerate(lines):
                if line.startswith('# Paths and directories'):
                    # Add after the section header
                    insert_pos = i + 1
                    while insert_pos < len(lines) and not lines[insert_pos].startswith('#'):
                        insert_pos += 1
                    
                    if not bullish_found:
                        lines.insert(insert_pos, 'BULLISH_DIR=./trained_model/bullish\n')
                        insert_pos += 1
                    if not bearish_found:
                        lines.insert(insert_pos, 'BEARISH_DIR=./trained_model/bearish\n')
                        insert_pos += 1
                    if not sentiment_found:
                        lines.insert(insert_pos, 'SENTIMENT_DIR=./trained_model/sentiment\n')
                    break
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        print(f"Updated model directory paths in {env_path}")
    else:
        print(f"Warning: .env file not found at {env_path}, skipping path updates.")

def verify_installation():
    """Verify that the models were correctly installed."""
    all_good = True
    for model_dir in ['bullish', 'bearish', 'sentiment']:
        path = os.path.join('trained_model', model_dir)
        if not os.path.exists(path) or not os.listdir(path):
            print(f"Warning: {path} is empty or does not exist.")
            all_good = False
    
    if all_good:
        print("Model installation verified successfully!")
    else:
        print("Some model directories are empty or missing.")
        print("Please download the models manually from the Google Drive link.")
        print("https://drive.google.com/file/d/1zjDwBqagqUPZ8H-igv4KlxdyFA8S4pe3/view?usp=sharing")

def main():
    """Main function."""
    print("Trading Models Downloader")
    print("========================")
    
    create_directories()
    check_requirements()
    download_models()
    verify_installation()
    
    print("\nDownload process completed.")
    print("If the models were not downloaded correctly, please download them manually from:")
    print("https://drive.google.com/file/d/1zjDwBqagqUPZ8H-igv4KlxdyFA8S4pe3/view?usp=sharing")

if __name__ == "__main__":
    main() 