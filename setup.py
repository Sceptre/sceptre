#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

with open("requirements.txt") as requirements_file:
    requirements = [
        requirement for requirement in requirements_file.read().split("\n")
        if requirement != ""
    ]


test_requirements = [
    "pytest==2.8.5",
    "moto==0.4.19",
    "mock==1.3.0",
    "behave==1.2.5"
]

setup_requirements = [
    "pytest-runner==2.6.2"
]

setup(
    name="sceptre",
    version="1.2.1",
    description="Cloud Provisioning Tool",
    long_description=readme + "\n\n" + history,
    author="Cloudreach",
    author_email="sceptre@cloudreach.com",
    license='Apache2',
    url="https://github.com/cloudreach/sceptre",
    packages=[
        "sceptre",
        "sceptre/resolvers",
        "sceptre/hooks"
    ],
    package_dir={
        "sceptre": "sceptre"
    },
    py_modules=["sceptre"],
    entry_points="""
        [console_scripts]
        sceptre=sceptre.cli:cli
    """,
    data_files=[
        ("sceptre/stack_policies", [
            "sceptre/stack_policies/lock.json",
            "sceptre/stack_policies/unlock.json"
        ])
    ],
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords="sceptre",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Environment :: Console",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5"
    ],
    test_suite="tests",
    tests_require=test_requirements,
    setup_requires=setup_requirements
)
