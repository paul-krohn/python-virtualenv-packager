# -*- coding: utf-8 -*-
#
# © 2019 Salesforce.com, Inc.
#
"""
Package setup for python-virtualenv-packager, aka ve-packager.
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from setuptools import setup, find_packages

# version: this requires an environment with dependencies installed.
from vep import __version__

# We use the version to construct the DOWNLOAD_URL.
NAME         = 've-packager'

# URL to the repository on Github.
REPO_URL     = 'https://github.com/krux/python-virtualenv-packager'
# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', __version__))

# Requirements
# If you have the option, run "pip install -r requirements.pip"

setup(
    name             = NAME,
    version          = __version__,
    author           = 'Paul Krohn',
    author_email     = 'pkrohn@salesforce.com',
    maintainer       = 'Paul Krohn',
    maintainer_email = 'pkrohn@krux.com',
    description      = 'Create an apt package from a python projet repo.',
    long_description = """
    Creates a virtualenv, installs dependencies, fixes paths, calls fpm to create a .deb package.
    """,
    url              = REPO_URL,
    download_url     = DOWNLOAD_URL,
    license          = 'All Rights Reserved.',
    packages         = find_packages(),
    install_requires = [
        "krux-stdlib",
        "sh",
        "virtualenv-tools"
    ],
    entry_points     = {
        'console_scripts': [
            've-packager = vep:main',
        ],
    },
)
