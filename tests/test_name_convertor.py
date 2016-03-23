import pytest

from pyp2rpm.name_convertor import NameConvertor
from pyp2rpm import settings


class TestUtils(object):

    def setup_method(self, method):
        self.ncf = NameConvertor('fedora')
        self.ncm = NameConvertor('mageia')

    @pytest.mark.parametrize(('input', 'expected_f', 'expected_m'), [
        ('python-spam', 'python-spam', 'python-spam'),
        ('python-PySpam', 'python-PySpam', 'python-pyspam'),
        ('python-spampy', 'python-spampy', 'python-spampy'),
        ('spam-python', 'python-spam', 'python-spam'),
        ('python26-foo', 'python-foo', 'python-foo'),
        ('foo-python26', 'python-foo', 'python-foo'),
        ('python3-foo', 'python-foo', 'python-foo'),
        ('foo-python3', 'python-foo', 'python-foo'),
    ])
    def test_rpm_name(self, input, expected_f, expected_m):
        assert self.ncf.rpm_name(input) == expected_f
        assert self.ncm.rpm_name(input) == expected_m

    @pytest.mark.parametrize(('name', 'version', 'expected'), [
        ('python-spam', None, 'python-spam'),
        ('pyspam', None, 'pyspam'),
        ('python-spam', '3', 'python3-spam'),
        ('pyspam', '26', 'python26-pyspam'),
        ('pyspam', settings.DEFAULT_PYTHON_VERSION, 'pyspam'),
        ('python-foo', '26', 'python26-foo'),
        ('python-foo', '3', 'python3-foo'),
        ('python2-foo', None, 'python-foo'),
        ('python2-foo', '3', 'python3-foo'),
        ('python26-foo', '3', 'python3-foo'),
        ('python26-foo', None, 'python-foo'),
        ('python-foo', '25', 'python25-foo'),
        ('python2-devel', 3, 'python3-devel'),
        ('python2-devel', None, 'python2-devel'),
    ])
    def test_rpm_versioned_name(self, name, version, expected):
        assert NameConvertor.rpm_versioned_name(name, version) == expected
