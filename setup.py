from setuptools import setup, find_packages

# Read the content of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fuzzit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here
        # "numpy>=1.18.0",
        # "pandas>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "fuzzit=fuzzit.cli:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A short description of your package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/your-repo",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/your-repo/issues",
        "Documentation": "https://github.com/yourusername/your-repo#readme",
        "Source Code": "https://github.com/yourusername/your-repo",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
    ],
    keywords="fuzzing, testing, development",
    python_requires=">=3.6",
    license="MIT",
)
