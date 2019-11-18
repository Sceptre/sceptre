#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sceptre import __version__
from setuptools import setup, find_packages
from os import path

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.md") as history_file:
    history = history_file.read()

install_requirements = [
    "boto3>=1.3,<2.0",
    "click==7.0",
    "PyYaml>=5.1,<6.0",
    "Jinja2>=2.8,<3",
    "jsonschema==3.1.1",
    "colorama==0.3.9",
    "packaging==16.8",
    "six>=1.11.0,<2.0.0",
    "networkx==2.1",
    "typing>=3.7.0,<3.8.0"
]

test_requirements = [
    "pytest>=3.2",
    "troposphere>=2.0.0",
    "moto==1.3.8",
    "mock==2.0.0",
    "behave==1.2.5",
    "freezegun==0.3.12"
]

setup_requirements = [
    "pytest-runner>=3"
]

setup(
    name="sceptre",
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
        "sceptre": "sceptre"
    },
    py_modules=["sceptre"],
    entry_points={
        "console_scripts": [
            'sceptre = sceptre.cli:cli'
        ],
        "sceptre.hooks": [
            "asg_scheduled_actions ="
            "sceptre.hooks.asg_scaling_processes:ASGScalingProcesses",
            "cmd = sceptre.hooks.cmd:Cmd"
        ],
        "sceptre.resolvers": [
            "environment_variable ="
            "sceptre.resolvers.environment_variable:EnvironmentVariable",
            "file_contents = sceptre.resolvers.file_contents:FileContents",
            "stack_output = sceptre.resolvers.stack_output:StackOutput",
            "stack_output_external ="
            "sceptre.resolvers.stack_output:StackOutputExternal"
        ],
        "sceptre.template_handlers": [
            "s3 = sceptre.template_handlers.s3:S3"
        ]
    },
    data_files=[
        (path.join("sceptre", "stack_policies"), [
            path.join("sceptre", "stack_policies", "lock.json"),
            path.join("sceptre", "stack_policies", "unlock.json")
        ])
    ],
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
