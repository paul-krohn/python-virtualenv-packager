# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import os
import unittest

#
# Third party libraries
#

from mock import patch

#
# Internal libraries
#
import vep


def my_isfile(filename):
    """
    Test function which calls os.path.isfile
    """
    return os.path.isfile(filename)


class CliOptionTests(unittest.TestCase):

    TEST_VERSION = '3.2.1'
    TEST_NAME = 'test-package-name'
    TEST_URL = 'https://github.com/org/repo'

    def setUp(self):
        """
        Deletes and then sets up a virtualenv; even with cached wheels, this will take much longer that usual test setup.
        In combination with `test_get_setup_option_version`, also tests `create_virtualenv`.
        """
        app = vep.Application(name='ve-packager')
        app.create_virtualenv()

    @patch('sys.argv', ['ve-packager', '--package-version', TEST_VERSION,
                        '--package-name', TEST_NAME,
                        '--repo-url', TEST_URL])
    def test_get_setup_option_version(self):
        """
        Test that when 'python setup.py --option_name' is passed in, get_setup_option returns the correct value,
        for each of name, url, and version.
        """
        app = vep.Application(name='ve-packager')
        self.assertEqual(self.TEST_VERSION, app.get_setup_option('version'))
        self.assertEqual(self.TEST_NAME, app.get_setup_option('name'))
        self.assertEqual(self.TEST_URL, app.get_setup_option('url'))

    @patch('os.path.isfile', side_effect=lambda f: f == './requirements.txt')
    def test_requirements_txt_file(self, _):
        """
        Test that, if a requirements.txt file exists, it will be chosen.
        """
        app = vep.Application('APP-NAME')
        self.assertEqual(app.args.pip_requirements, None)
        self.assertEqual(app._pip_requirements_filename(), './requirements.txt')

    @patch('os.path.isfile', side_effect=lambda f: f == './requirements.pip')
    def test_requirements_pip_file(self, _):
        """
        Test that, if a requirements.pip file exists, it will be chosen.
        """
        app = vep.Application('APP-NAME')
        self.assertEqual(app.args.pip_requirements, None)
        self.assertEqual(app._pip_requirements_filename(), './requirements.pip')

    @patch('sys.argv', ['ve-packager', '--pip-requirements', 'my-requirements.txt'])
    @patch('os.path.isfile', side_effect=lambda f: f == 'my-requirements.txt')
    def test_requirements_my_file(self, _):
        """
        Test that supplied requirements file is honored.
        """
        app = vep.Application('APP-NAME')
        self.assertEqual(app.args.pip_requirements, 'my-requirements.txt')
