import pytest

from flexmock import flexmock

from pyp2rpm.convertor import Convertor
from pyp2rpm.exceptions import *
from pyp2rpm.metadata_extractors import *
from pyp2rpm.package_getters import *

tests_dir = os.path.split(os.path.abspath(__file__))[0]

class TestConvertor(object):
    client = flexmock(package_releases = lambda n: n == 'spam' and ['0.1'] or [])
    Convertor.client = client # flexmock can't mock properties yet 

    @pytest.mark.parametrize(('sf', 'n', 'g'), [
        ('pypi', 'spam', PypiDownloader),
        ('%s/test_data/restsh-0.1.tar.gz' % tests_dir, '', LocalFileGetter)
    ])
    def test_getter_good_data(self, sf, n, g):
        c = Convertor(source_from = sf, name = n)
        assert isinstance(c.getter, g)

    @pytest.mark.parametrize(('sf', 'n', 'expected'), [
        ('pypi', 'eggs', NoSuchPackageException),
        ('spam source', 'beans', NoSuchSourceException),
        ('/spam/beans/eggs/ham', '', NoSuchSourceException)
    ])
    def test_getter_bad_data(self, sf, n, expected):
        with pytest.raises(expected):
            c = Convertor(source_from = sf, name = n)
            c.getter

    @pytest.mark.parametrize(('sf', 'n', 'mf', 'expected'), [
        ('pypi', 'spam', 'pypi', PypiMetadataExtractor),
        ('%s/test_data/restsh-0.1.tar.gz' % tests_dir, '', 'something other than pypi', LocalMetadataExtractor)
    ])
    def test_get_metadata_extractor(self, sf, n, mf, expected):
        c = Convertor(source_from = sf, name = n, metadata_from = mf)
        assert isinstance(c.get_metadata_extractor('spamfile'), expected)
