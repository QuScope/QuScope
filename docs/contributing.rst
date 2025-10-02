============
Contributing
============

We welcome contributions to QuScope! This guide will help you get started.

**How to Contribute**
========================

There are many ways to contribute to QuScope:

- 🐛 **Report bugs** via GitHub issues
- **Suggest features** and enhancements  
- **Improve documentation**
- 🧪 **Add tests** for better coverage
- 💻 **Submit code** fixes and features
- **Create examples** and tutorials

**Getting Started**
======================

1. **Fork the Repository**
   
   Fork the QuScope repository on GitHub and clone your fork:
   
   .. code-block:: bash
   
      git clone https://github.com/YOUR_USERNAME/quantum_algo_microscopy.git
      cd quantum_algo_microscopy

2. **Set Up Development Environment**
   
   Create a virtual environment and install development dependencies:
   
   .. code-block:: bash
   
      python -m venv quscope_dev
      source quscope_dev/bin/activate  # On Windows: quscope_dev\Scripts\activate
      pip install -e ".[dev,docs]"

3. **Run Tests**
   
   Ensure everything works:
   
   .. code-block:: bash
   
      pytest tests/
      python -m doctest src/quscope/image_processing/quantum_encoding.py

📋 **Development Guidelines**
=============================

**Code Style**
- Follow PEP 8 style guidelines
- Use Black for code formatting: ``black src/ tests/``
- Use isort for import sorting: ``isort src/ tests/``
- Maximum line length: 88 characters (Black default)

**Documentation**
- Write docstrings for all public functions and classes
- Use Google-style docstrings
- Include usage examples in docstrings when helpful
- Update documentation when adding new features

**Testing**
- Write tests for new functionality using pytest
- Aim for >90% test coverage
- Include both unit tests and integration tests
- Test edge cases and error conditions

**Git Workflow**
- Create feature branches from ``main``
- Use descriptive commit messages
- Keep commits focused and atomic
- Include issue numbers in commit messages when applicable

🧪 **Running Tests**
====================

.. code-block:: bash

   # Run all tests
   pytest tests/
   
   # Run with coverage
   pytest tests/ --cov=src/quscope --cov-report=html
   
   # Run specific test file
   pytest tests/test_quantum_encoding.py
   
   # Run doctests
   python -m doctest src/quscope/image_processing/quantum_encoding.py -v

🔧 **Development Tools**
========================

**Pre-commit Hooks**

Set up pre-commit hooks to automatically format code:

.. code-block:: bash

   pre-commit install

**Linting**

.. code-block:: bash

   # Check code style
   flake8 src/ tests/
   
   # Type checking
   mypy src/quscope/

**Documentation Building**

.. code-block:: bash

   cd docs/
   make html
   # Open docs/_build/html/index.html

**Submitting Changes**
=========================

1. **Create a Branch**
   
   .. code-block:: bash
   
      git checkout -b feature/your-feature-name

2. **Make Changes**
   
   - Write your code
   - Add/update tests
   - Update documentation
   - Run tests locally

3. **Commit Changes**
   
   .. code-block:: bash
   
      git add .
      git commit -m "Add feature: describe your changes"

4. **Push and Create PR**
   
   .. code-block:: bash
   
      git push origin feature/your-feature-name
   
   Then create a Pull Request on GitHub.

🐛 **Reporting Issues**
=======================

When reporting bugs, please include:

- **Environment**: Python version, OS, QuScope version
- **Steps to reproduce**: Minimal code example
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Full traceback if applicable

**Feature Requests**
=======================

For feature requests, please describe:

- **Use case**: Why do you need this feature?
- **Proposed solution**: How should it work?
- **Alternatives**: Have you considered other approaches?
- **Additional context**: Any relevant background information

🏷️ **Release Process**
======================

For maintainers:

1. Update version in ``src/__init__.py`` and ``pyproject.toml``
2. Update ``CHANGELOG.md`` with new features and fixes  
3. Create a git tag: ``git tag -a v0.1.0 -m "Release v0.1.0"``
4. Push tag: ``git push origin v0.1.0``
5. Build and upload to PyPI: ``python -m build && twine upload dist/*``

📞 **Getting Help**
===================

- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Issues**: Report bugs via GitHub Issues  
- 📧 **Email**: Contact maintainers for sensitive issues

Thank you for contributing to QuScope! 🙏
