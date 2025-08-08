#!/bin/bash
# Post-release script to update README after PyPI publication

echo "🎉 Post-Release Updates for QuScope"
echo "==================================="

echo ""
echo "Updating README.md to reflect PyPI availability..."

# Update the header note
sed -i.bak 's/> \*\*Note\*\*: QuScope v0.1.0 is preparing for initial PyPI release. Install from source until PyPI package is available./> \*\*Status\*\*: QuScope v0.1.0 is now available on PyPI! 🎉/' README.md

# Update installation section
sed -i.bak 's/### From PyPI (Coming Soon)/### From PyPI (Recommended)/' README.md
sed -i.bak 's/> \*\*Status\*\*: QuScope v0.1.0 will be available on PyPI after the first official release is created on GitHub./> \*\*Latest\*\*: QuScope v0.1.0 is now available on PyPI./' README.md
sed -i.bak 's/pip install quscope  # Available after v0.1.0 release/pip install quscope/' README.md

# Update quick start
sed -i.bak 's/### After PyPI Release (Coming Soon)/### From PyPI (Recommended)/' README.md
sed -i.bak 's/### Current Installation (Development)/### Development Installation/' README.md

# Add PyPI badge back
sed -i.bak 's/\[\!\[GitHub release\]/\[\!\[PyPI version\](https:\/\/badge.fury.io\/py\/quscope.svg)\](https:\/\/badge.fury.io\/py\/quscope)\n\[\!\[GitHub release\]/' README.md

# Clean up backup files
rm README.md.bak

echo "✅ README.md updated successfully!"
echo ""
echo "📝 Don't forget to:"
echo "1. Commit and push the updated README"
echo "2. Verify the PyPI package: https://pypi.org/project/quscope/"
echo "3. Test installation: pip install quscope"
