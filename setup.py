# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#
"""
Package setup for krux-rundeck-utils
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from setuptools import setup, find_packages
from pip.req import parse_requirements
import os

# We use the version to construct the DOWNLOAD_URL.
VERSION      = '0.0.1'
NAME         = 've-packager'

# URL to the repository on Github.
REPO_URL     = 'https://github.com/krux/hoarder'
# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))

# Requirements
# We want to install all the dependencies of the library as well, but we
# don't want to duplicate the dependencies both here and in
# requirements.pip. Instead we parse requirements.pip to pull in our
# dependencies.
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = os.path.join(BASE_DIR, 'requirements.pip')
# start with pip, to suppress a pep8 warning from the import above
DEPENDENCIES = ['pip', 'sh']
# then loop over the requirements from the file
for package in parse_requirements(REQUIREMENTS):
    DEPENDENCIES.append(str(package.req))

setup(
    name             = NAME,
    version          = VERSION,
    author           = 'Paul Krohn',
    author_email     = 'pkrohn@krux.com',
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
    install_requires = DEPENDENCIES,
    entry_points     = {
        'console_scripts': [
            've-packager = vep:main',
        ],
    },
)
