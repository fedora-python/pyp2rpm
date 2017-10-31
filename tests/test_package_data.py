import pytest

from pyp2rpm.package_data import PackageData


class TestPackageData(object):

    @pytest.mark.parametrize(('s', 'expected'), [
        ('Spam.', 'Spam'),
        ('Spam', 'Spam'),
    ])
    def test_summary_with_dot(self, s, expected):
        pd = PackageData('spam', 'spam', 'python-spam', 'spam')
        pd.summary = s
        assert pd.summary == expected

    @pytest.mark.parametrize('name', [
        'summary', 'description', ])
    def test_set_none_value(self, name):
        pd = PackageData('spam', 'spam', 'python-spam', 'spam')
        setattr(pd, name, None)
        actual = getattr(pd, name)
        assert actual == 'TODO:'

    def test_get_nonexistent_attribute(self):
        pd = PackageData('spam', 'spam', 'python-spam', 'spam')
        assert pd.eggs == 'TODO:'

    @pytest.mark.parametrize(('n', 'expected'), [
        ('py-spam', 'py_spam'),
        ('py_spam', 'py_spam'),
        ('spam', 'spam'),
    ])
    def test_underscored_name(self, n, expected):
        pd = PackageData('spam', n, 'python-spam', 'spam')
        assert pd.underscored_name == expected

    @pytest.mark.parametrize(('key', 'init', 'update_data', 'expected'), [
        ('name', 'Spam', {'name': 'Spam'}, 'Spam'),
        ('name', ['Spam'], {'name': ['Spam2']}, ['Spam', 'Spam2']),
        ('name', set(['Spam']), {'name': set(['Spam2'])},
         set(['Spam', 'Spam2'])),
        ('name', [], {'name': ['Spam', 'Spam2']}, ['Spam', 'Spam2']),
        ('name', False, {'name': True}, False),
        ('name', 'Spam', {'name': ''}, 'Spam'),
        ('name', 'Spam', {'name': 'Spam2'}, 'Spam'),
        ('doc_files', 'Spam', {'doc_files': set(['README'])}, set(['README'])),
    ])
    def test_update_attr(self, key, init, update_data, expected):
        pd = PackageData('spam', init, 'python-spam', 'spam')
        pd.set_from(update_data, update=True)
        assert pd.data[key] == expected
