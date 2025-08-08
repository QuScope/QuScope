"""Setup configuration for quantum algorithm microscopy package."""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Get version from __init__.py
def get_version():
    import re
    try:
        with open("src/__init__.py", "r") as fp:
            content = fp.read()
            version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
            if version_match:
                return version_match.group(1)
    except FileNotFoundError:
        pass
    return "0.1.0"

version_str = get_version()

setup(
    name="quantum-algo-microscopy",
    version=version_str,
    author="Roberto dos Reis and Sean Lam",
    author_email="roberto@example.com",
    description="Quantum Algorithm Microscopy - Advanced quantum computing analysis tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robertoreis/quantum_algo_microscopy",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
