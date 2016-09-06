import pytest

from command.extract_dist import to_list


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
        assert to_list(var) == expected
