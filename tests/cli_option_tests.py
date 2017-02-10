# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest

#
# Third party libraries
#

from mock import patch

#
# Internal libraries
#
import vep


class CliOptionTests(unittest.TestCase):

    TEST_VERSION = '3.2.1'
    TEST_NAME = 'test-package-name'
    TEST_URL = 'https://github.com/org/repo'

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

