import pytest

from flexmock import flexmock

from pyp2rpm.command.extract_dist import to_list, extract_dist


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

    @pytest.mark.parametrize(('metadata'), [
        ({'foo': lambda: None}),
        ({'foo': ['bar', lambda: None]}),
    ])
    def test_serializing_metadata_to_stdout_success(self, metadata, capsys):
        flexmock(extract_dist).should_receive('__init__').and_return(None)
        command = extract_dist()
        command.metadata = metadata
        command.stdout = True
        command.run()
        out, err = capsys.readouterr()
        assert not err
