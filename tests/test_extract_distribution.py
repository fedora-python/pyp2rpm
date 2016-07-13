import pytest

from pyp2rpm.extract_distribution import extract_distribution


class TestExtractDistribution(object):

    @pytest.mark.parametrize(('var', 'expected'), [
        (['pkg'], ['pkg']),
        (None, []),
        ('pkg >= 2.5\npkg2', ['pkg >= 2.5', 'pkg2']),
        (('pkg'), ['pkg']),
        (('pkg',), ['pkg']),
        ((p for p in ('pkg',)), ['pkg']),
    ])
    def test_list(self, var, expected):
        assert extract_distribution._list(var) == expected
