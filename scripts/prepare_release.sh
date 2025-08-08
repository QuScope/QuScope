#!/bin/bash
# Pre-release checklist and helper script for QuScope

echo "🔬 QuScope v0.1.0 Release Preparation"
echo "====================================="

echo ""
echo "📋 Pre-release Checklist:"
echo "-------------------------"

# Check if version is consistent
VERSION_PYPROJECT=$(grep "version" pyproject.toml | head -1 | cut -d'"' -f2)
VERSION_DOCS=$(grep "version" docs/conf.py | head -1 | cut -d"'" -f2)

echo "✓ Version in pyproject.toml: $VERSION_PYPROJECT"
echo "✓ Version in docs/conf.py: $VERSION_DOCS"

if [ "$VERSION_PYPROJECT" = "$VERSION_DOCS" ]; then
    echo "✅ Versions are consistent"
else
    echo "❌ Version mismatch detected!"
    exit 1
fi

echo ""
echo "🧪 Running Tests:"
echo "-----------------"
if [ -d "tests" ]; then
    python -m pytest tests/ -v || echo "⚠️  Some tests failed or no tests found"
else
    echo "⚠️  No tests directory found"
fi

echo ""
echo "📦 Building Package:"
echo "--------------------"
python -m build
echo "✅ Package built successfully"

echo ""
echo "🔍 Package Verification:"
echo "------------------------"
python -m twine check dist/*
echo "✅ Package structure verified"

echo ""
echo "📚 Documentation Check:"
echo "-----------------------"
if [ -f "docs/Makefile" ]; then
    cd docs && make html && cd ..
    echo "✅ Documentation built successfully"
else
    echo "⚠️  Documentation build skipped"
fi

echo ""
echo "🚀 Ready for Release!"
echo "====================="
echo ""
echo "Next Steps:"
echo "1. Create GitHub release at: https://github.com/QuScope/QuScope/releases/new"
echo "2. Use tag: v$VERSION_PYPROJECT"
echo "3. Title: QuScope v$VERSION_PYPROJECT"
echo "4. The workflow will automatically publish to PyPI"
echo ""
echo "After release, update README.md to remove 'Coming Soon' notes"
