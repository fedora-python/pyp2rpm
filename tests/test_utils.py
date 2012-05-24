import pytest

from pyp2rpmlib import utils
from pyp2rpmlib import settings

class TestUtils(object):
    @pytest.mark.parametrize(("input", "expected"), [
        ("python-spam", "python-spam"),
        ("PySpam", "PySpam"),
        ("spampy", "spampy"),
        ('spam-python', 'python-spam')
    ])
    def test_rpm_name(self, input, expected):
        assert utils.rpm_name(input) == expected

    @pytest.mark.parametrize(('name', 'version', 'expected'), [
        ('python-spam', None, 'python-spam'),
        ('pyspam', None, 'pyspam'),
        ('python-spam', '3', 'python3-spam'),
        ('pyspam', '26', 'python26-pyspam'),
        ('pyspam', settings.DEFAULT_PYTHON_VERSION, 'pyspam'),
    ])
    def test_rpm_versioned_name(self, name, version, expected):
        assert utils.rpm_versioned_name(name, version) == expected

    def test_memoize_by_args(self):
        assert self.memoized(1) == 1
        assert hasattr(self, 'memoized_called')
        assert self.memoized(1) == 1

    @utils.memoize_by_args
    def memoized(self, num):
        if hasattr(self, "memoized_called"):
            raise BaseException('This should not have been called!')
        else:
            setattr(self, "memoized_called", True)

        return num

    @pytest.mark.parametrize(("input", "expected"), [
        ([], ""),
        (['License :: OSI Approved :: Python Software Foundation License'], 'Python'),
        (['Classifier: License :: OSI Approved :: Python Software Foundation License'], 'Python'),
        (['License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)', 'License :: OSI Approved :: MIT License'], 'GPLv2+ and MIT'),
    ])
    def test_license_from_trove(self, input, expected):
        assert utils.license_from_trove(input) == expected
