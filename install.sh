#!/bin/bash

# Svitlo CLI Installation Script
# This script installs Svitlo CLI application system-wide

set -e

echo "💡 Svitlo CLI Installation Script"
echo "================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ Error: pip is not installed. Please install pip first."
    exit 1
fi

# Determine pip command
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

echo "✅ Found Python: $(python3 --version)"
echo "✅ Found pip: $($PIP_CMD --version)"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Installation directory: $SCRIPT_DIR"

# Install the package in development mode
echo "📦 Installing Svitlo CLI..."
cd "$SCRIPT_DIR"

# Upgrade pip and install setuptools/wheel if needed
echo "🔄 Upgrading pip and installing build tools..."
$PIP_CMD install --upgrade pip setuptools wheel

# Install the package
echo "🔧 Installing Svitlo CLI system-wide..."
$PIP_CMD install -e .

# Install Playwright browsers
echo "🌐 Installing Playwright browsers (this may take a moment)..."
playwright install

# Verify installation
echo "✅ Verifying installation..."
if command -v svitlo-cli &> /dev/null; then
    echo "🎉 Installation successful!"
    echo ""
    echo "You can now run Svitlo CLI from anywhere with:"
    echo "  svitlo-cli"
    echo ""
    echo "Or with Python directly:"
    echo "  python3 -m svitlo-cli"
    echo ""
    echo "To uninstall, run:"
    echo "  $PIP_CMD uninstall svitlo-cli"
else
    echo "⚠️  Installation completed but 'svitlo-cli' command not found in PATH."
    echo "You may need to restart your terminal or run:"
    echo "  $PIP_CMD install --force-reinstall svitlo-cli"
fi