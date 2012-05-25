import time

import pytest

from flexmock import flexmock

from pyp2rpmlib.package_data import *

class TestPackageData(object):
    @pytest.mark.parametrize(('s', 'expected'), [
            ('Spam.', 'Spam'),
            ('Spam', 'Spam'),
    ])
    def test_summary_with_dot(self, s, expected):
        pd = PackageData('spam', 'spam', 'spam')
        pd.summary = s
        assert pd.summary == expected

    def test_get_nonexistent_attribute(self):
        pd = PackageData('spam', 'spam', 'spam')
        assert pd.eggs == 'TODO:'

    @pytest.mark.parametrize(('n', 'expected'), [
        ('py-spam', 'py_spam'),
        ('py_spam', 'py_spam'),
        ('spam', 'spam'),
    ])
    def test_underscored_name(self, n, expected):
        pd = PackageData('spam', n, 'spam')
        assert pd.underscored_name == expected
