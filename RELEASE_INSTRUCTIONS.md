# QuScope v0.1.0 Release Instructions

## Step 1: Tag Release ✓
```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```
**Status**: COMPLETE - Tag exists and pushed to remote

## Step 2: Build Distribution Packages ✓
```bash
# Clean previous builds
rm -rf dist/ build/ src/*.egg-info

# Build source distribution and wheel
python -m build
```

**Built files**:
- `dist/quscope-0.1.0.tar.gz` (139KB)
- `dist/quscope-0.1.0-py3-none-any.whl` (125KB)

**Verification**: Both packages passed `twine check` ✓

## Step 3: Publish to PyPI
### Test PyPI (Recommended first)
```bash
# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quscope
```

### Production PyPI
```bash
# Upload to PyPI
python -m twine upload dist/*

# Verify installation
pip install quscope
```

**Requirements**:
- PyPI account credentials
- API token configured in `~/.pypirc` or use `--username` and `--password` flags

**Status**: READY TO PUBLISH

## Step 4: Update ReadTheDocs ✓

### Automatic Updates
ReadTheDocs is configured to automatically build from:
- Repository: https://github.com/QuScope/QuScope
- Config file: `.readthedocs.yaml`
- Branch: main (auto-builds on push)
- Tag: v0.1.0 (auto-builds on tag creation)

### Manual Verification
1. Visit: https://readthedocs.org/projects/quscope/
2. Check "Builds" tab for successful v0.1.0 build
3. Verify documentation at: https://quscope.readthedocs.io/en/v0.1.0/
4. Ensure "latest" points to v0.1.0

**Status**: Auto-configured, builds should trigger automatically

## Step 5: Create GitHub Release ✓
```bash
gh release create v0.1.0 \
  --title "QuScope v0.1.0 - Initial Release" \
  --notes-file RELEASE_NOTES.md \
  dist/quscope-0.1.0.tar.gz \
  dist/quscope-0.1.0-py3-none-any.whl
```

**Release URL**: https://github.com/QuScope/QuScope/releases/tag/v0.1.0

**Status**: COMPLETE - Release created with comprehensive notes and distribution files attached

## Post-Release Checklist

### Documentation
- [ ] Verify documentation builds on ReadTheDocs
- [ ] Check all API references are accessible
- [ ] Verify notebooks render correctly
- [ ] Confirm installation instructions work

### PyPI
- [ ] Test installation: `pip install quscope`
- [ ] Verify package metadata on PyPI page
- [ ] Check that dependencies install correctly
- [ ] Test example code from README

### GitHub
- [x] Tag created and pushed
- [x] Release published with notes
- [x] Distribution files attached
- [ ] Close any resolved issues
- [ ] Update project board if applicable

### Communication
- [ ] Announce release on relevant channels
- [ ] Update project website (if applicable)
- [ ] Post to social media/academic networks
- [ ] Notify collaborators and users

## Troubleshooting

### Build Issues
If build fails:
```bash
# Check package structure
python -m build --sdist --wheel --outdir dist/ .

# Validate with check-manifest
pip install check-manifest
check-manifest
```

### PyPI Upload Issues
If upload fails:
```bash
# Check credentials
cat ~/.pypirc

# Verify package
python -m twine check dist/*

# Use verbose mode
python -m twine upload --verbose dist/*
```

### ReadTheDocs Issues
If docs don't build:
1. Check `.readthedocs.yaml` configuration
2. Verify `docs/requirements.txt` has all dependencies
3. Check build logs at https://readthedocs.org/projects/quscope/builds/
4. Ensure all Sphinx extensions are installed

## Next Steps

### v0.1.1 Planning
1. Monitor user feedback and issues
2. Plan bug fixes and minor improvements
3. Update CHANGELOG.md
4. Set up CI/CD for automated releases

### v0.2.0 Planning
1. Review feature requests
2. Plan major enhancements
3. Update documentation for new features
4. Prepare migration guide if breaking changes

---

**Release Date**: October 2, 2025  
**Released by**: Roberto dos Reis  
**Release Status**: IN PROGRESS - Step 3 (PyPI) pending
