import pytest

from pyp2rpm import utils
from pyp2rpm import settings


class TestUtils(object):

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
        (['License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
          'License :: OSI Approved :: MIT License'], 'GPLv2+ and MIT'),
    ])
    def test_license_from_trove(self, input, expected):
        assert utils.license_from_trove(input) == expected

    @pytest.mark.parametrize(('input', 'expected'), [
        (set(['script', 'script2', 'script-0.1']), set(['script', 'script2'])),
        (set([]), set([])),
        (set(['script-a']), set(['script-a'])),
        (set(['script-3', 'script-3.4']), set([])),
        (set(['script-3.4']), set([])),
    ])
    def test_remove_major_minor_suffix(self, input, expected):
        assert utils.remove_major_minor_suffix(input) == expected

    @pytest.mark.parametrize(('input', 'expected'), [
        ([['Requires', 'pkg'], ['Requires', 'pkg2']],
         [['BuildRequires', 'pkg'], ['BuildRequires', 'pkg2']]),
        ([['Requires', 'pkg', '>=', '1.4.29'], ['Requires', 'python-setuptools']],
         [['BuildRequires', 'pkg', '>=', '1.4.29'], ['BuildRequires',
                                                     'python-setuptools']]),
        ([], []),
        ([[], []], [[], []]),
    ])
    def test_runtime_to_build(self, input, expected):
        assert utils.runtime_to_build(input) == expected

    @pytest.mark.parametrize(('input', 'expected'), [
        ([['Requires', 'pkg'], ['Requires', 'pkg']], [['Requires', 'pkg']]),
        ([['Requires', 'pkg']], [['Requires', 'pkg']]),
        ([['Requires', 'pkg'], ['Requires', 'pkg2'], ['Requires', 'pkg']],
         [['Requires', 'pkg'], ['Requires', 'pkg2']]),
        ([], []),
        ([[], []], [[]]),
        ([[1], [2], [3], [2]], [[1], [2], [3]]),
    ])
    def test_unique_deps(self, input, expected):
        assert utils.unique_deps(input) == expected
