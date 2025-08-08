#!/bin/bash
# Build and publish script for QuScope

set -e

echo "🔨 Building QuScope package..."

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

echo "✅ Build complete!"

# Check the package
echo "🔍 Checking package..."
python -m twine check dist/*

echo "📦 Package contents:"
tar -tzf dist/*.tar.gz | head -20

echo ""
echo "🚀 To publish to PyPI:"
echo "   Test PyPI: python -m twine upload --repository testpypi dist/*"
echo "   Real PyPI: python -m twine upload dist/*"
echo ""
echo "Make sure you have your PyPI API token configured!"
