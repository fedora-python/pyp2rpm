import pytest

from pyp2rpmlib import utils

class TestUtils(object):
    @pytest.mark.parametrize(("input", "expected"), [
        ("python-spam", "python-spam"),
        ("PySpam", "PySpam"),
        ("spampy", "spampy"),
    ])
    def test_rpm_name(self, input, expected):
        assert utils.rpm_name(input) == expected

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
