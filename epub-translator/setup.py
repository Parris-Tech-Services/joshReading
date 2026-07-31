"""Project setup configuration."""

from setuptools import setup, find_packages

setup(
    name="epub-translator",
    version="0.1.0",
    description="Translate French EPUBs to English with preservation of structure",
    author="Josh",
    python_requires=">=3.12",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.6.0",
        "ebooklib>=0.18.0",
        "lxml>=4.9.0",
        "BeautifulSoup4>=4.12.0",
        "argostranslate>=1.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "epub-translator=epub_translator.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Natural Language :: French",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Graphics :: Viewers",
        "Topic :: Office/Business",
        "Topic :: Text Processing",
    ],
)
