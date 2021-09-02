#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
from setuptools import setup, find_packages


def read_file(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read_file(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


install_requirements = [
    "boto3>=1.3,<2.0",
    "click>=7.0,<9.0",
    "PyYaml>=5.1,<6.0",
    "Jinja2>=2.8,<3",
    "colorama>=0.3.9",
    "packaging>=16.8,<17.0",
    "sceptre-cmd-resolver>=1.1.3,<2",
    "sceptre-file-resolver>=1.0.4,<2",
    "six>=1.11.0,<2.0.0",
    "networkx>=2.4,<2.6"
]

setup(
    name="sceptre",
    version=get_version("sceptre/__init__.py"),
    description="Cloud Provisioning Tool",
    long_description=read_file("README.md"),
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
        ]
    },
    data_files=[
        (os.path.join("sceptre", "stack_policies"), [
            os.path.join("sceptre", "stack_policies", "lock.json"),
            os.path.join("sceptre", "stack_policies", "unlock.json")
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    test_suite="tests",
    install_requires=install_requirements,
)
