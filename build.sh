#!/bin/bash
echo "Building PavanBrowser for Linux..."
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# Build the executable
echo ""
echo "Building executable..."
pyinstaller PavanBrowser.spec --clean

echo ""
echo "Build complete! Executable is in the dist/PavanBrowser folder"
