#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from project_info import __version__

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.md") as history_file:
    history = history_file.read()

install_requirements = [
    "click==7.0",
    "colorama==0.3.9",
    "packaging==16.8",
    "six>=1.11.0,<2.0.0",
    "PyYaml>=5.1,<6.0",
    "sceptre-core @ git+https://github.com/Sceptre/sceptre-core.git@master"
]

test_requirements = [
    "pytest>=3.2",
    "moto==1.3.8",
    "mock==2.0.0",
    "behave==1.2.5",
    "freezegun==0.3.12"
]

setup_requirements = [
    "pytest-runner>=3"
]

setup(
    name="sceptre-cli",
    version=__version__,
    description="Cloud Provisioning Tool",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Cloudreach",
    author_email="sceptre@cloudreach.com",
    license='Apache2',
    url="https://github.com/cloudreach/sceptre",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_dir={
        "sceptre": "cli"
    },
    py_modules=["sceptre-cli"],
    entry_points={
        "console_scripts": [
            'sceptre = cli:cli'
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="sceptre",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Environment :: Console",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ],
    test_suite="tests",
    install_requires=install_requirements,
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    extras_require={
        "test": test_requirements
    }
)
