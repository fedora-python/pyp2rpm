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

    @pytest.mark.parametrize(('input', 'expected'), [
        (['script', 'script2', 'script-0.1'], ['script', 'script2']),
        ([], []),
        (['script-a'], ['script-a']),
        (['script-3', 'script-3.4'], []),
        (['script-3.4'], []),
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
