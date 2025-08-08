# GitHub Workflows for QuScope

This directory contains GitHub Actions workflows for the QuScope project.

## Workflows

### `workflow.yml` - PyPI Publishing
- **Purpose**: Automatically publishes the package to PyPI when a release is created
- **Trigger**: When a GitHub release is published
- **Environment**: Uses the `pypi` environment (needs to be configured in repository settings)
- **Features**:
  - Runs tests across Python 3.9-3.12 before publishing
  - Uses trusted publishing (no API tokens needed)
  - Builds and verifies the package before upload

### `tests.yml` - Continuous Integration
- **Purpose**: Runs tests and checks on every push and pull request
- **Trigger**: Push to main/develop branches, PRs to main
- **Features**:
  - Tests across Python 3.9-3.12
  - Linting with flake8
  - Documentation building
  - Import verification

## Setup Instructions

### 1. Configure PyPI Trusted Publishing

1. Go to [PyPI](https://pypi.org) and log in
2. Go to "Your projects" → "Manage" → "Publishing"
3. Add a new trusted publisher with:
   - **Owner**: QuScope
   - **Repository name**: QuScope
   - **Workflow name**: workflow.yml
   - **Environment name**: pypi

### 2. Configure GitHub Environment

1. Go to your GitHub repository settings
2. Navigate to "Environments"
3. Create a new environment named `pypi`
4. Optionally add protection rules (recommended):
   - Required reviewers
   - Deployment branches (only main)

### 3. Create a Release

To publish to PyPI:

1. Go to GitHub → Releases → "Create a new release"
2. Create a new tag (e.g., `v0.1.0`)
3. Fill in release notes
4. Click "Publish release"

The workflow will automatically:
- Run tests
- Build the package
- Publish to PyPI

## Manual Publishing

If you prefer manual publishing:

```bash
# Build the package
./scripts/build_and_publish.sh

# Upload to PyPI (requires API token)
python -m twine upload dist/*
```
