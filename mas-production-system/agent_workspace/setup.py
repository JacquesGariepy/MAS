"""
Setup configuration for sample_lib
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sample_lib",
    version="0.1.0",
    author="MAS Swarm",
    author_email="swarm@mas-system.ai",
    description="A sample Python library created by the unified swarm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mas-swarm/sample_lib",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[],
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
)
