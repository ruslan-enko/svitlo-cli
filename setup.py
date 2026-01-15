#!/usr/bin/env python3

from setuptools import setup, find_packages
import os


# Read README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Dependencies
DEPENDENCIES = [
    "textual>=0.47.0",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "playwright>=1.48.0",
]

setup(
    name="svitlo-cli",
    version="0.44",
    author="Enko",
    author_email="",
    description="Terminal TUI app for monitoring power outage schedules in Lviv",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ruslan-enko/svitlo-cli",
    py_modules=[
        "main",
        "screens",
    ],
    packages=[
        "core",
        "layout",
        "ui",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=DEPENDENCIES,
    entry_points={
        "console_scripts": [
            "svitlo-cli=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)