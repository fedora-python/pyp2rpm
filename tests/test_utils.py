import pytest
import os
from flexmock import flexmock
try:
    import rpm
except ImportError:
    rpm = None

from pyp2rpm import utils


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
        ([['Requires', 'pkg', '>=', '1.4.29'],
          ['Requires', 'python-setuptools']],
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

    def test_rpm_eval(self):
        if os.path.exists('/usr/bin/rpm'):
            assert utils.rpm_eval('macro') == 'macro'
        else:
            assert utils.rpm_eval('macro') == ''

    def test_get_default_save_path_eval_success(self):
        if rpm:
            flexmock(rpm).should_receive(
                'expandMacro').once().and_return('foo')
        else:
            flexmock(utils).should_receive('rpm_eval').once().and_return('foo')
        assert utils.get_default_save_path() == 'foo'

    def test_get_default_save_path_eval_fail(self):
        if rpm:
            flexmock(rpm).should_receive(
                'expandMacro').once().and_return('foo')
        else:
            flexmock(utils).should_receive('rpm_eval').once().and_return('')
            flexmock(os).should_receive('path.expanduser').once(
            ).and_return('foo')
        assert utils.get_default_save_path() == 'foo'
