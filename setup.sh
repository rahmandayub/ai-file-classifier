#!/bin/bash

# AI File Classifier - Setup Script for Linux/macOS
# This script sets up the virtual environment and installs dependencies

set -e  # Exit on error

echo "=========================================="
echo "AI File Classifier - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check if Python version is 3.10 or higher
REQUIRED_VERSION="3.10"
if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "Error: Python 3.10 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version check passed"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install package
echo "Installing AI File Classifier..."
pip install -e . --quiet
echo "✓ Package installed"
echo ""

# Verify installation
echo "Verifying installation..."
if python -m src.main --version &> /dev/null; then
    echo "✓ Installation verified"
else
    echo "⚠ Warning: Could not verify installation"
fi
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "  Please edit .env and add your API key if using OpenAI"
else
    echo ".env file already exists"
fi
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start using the classifier, run:"
echo "  python -m src.main classify <source> <destination>"
echo ""
echo "For help, run:"
echo "  python -m src.main classify --help"
echo ""
