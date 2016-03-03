import pytest

from flexmock import flexmock

from pyp2rpm.convertor import Convertor
from pyp2rpm.exceptions import *
from pyp2rpm.metadata_extractors import *
from pyp2rpm.package_getters import *

tests_dir = os.path.split(os.path.abspath(__file__))[0]

class TestConvertor(object):
    client = flexmock(package_releases = lambda n: n == 'spam' and ['0.1'] or [])
    Convertor._client = client # flexmock can't mock properties yet

    @pytest.mark.parametrize(('sf', 'g'), [
        ('spam', PypiDownloader),
        ('%s/test_data/restsh-0.1.tar.gz' % tests_dir, LocalFileGetter)
    ])
    def test_getter_good_data(self, sf, g):
        c = Convertor(package=sf)
        assert isinstance(c.getter, g)

    @pytest.mark.parametrize(('sf', 'expected'), [
        ('eggs', NoSuchPackageException),
        ('/spam/beans/eggs/ham', NoSuchPackageException)
    ])
    def test_getter_bad_data(self, sf, expected):
        with pytest.raises(expected):
            c = Convertor(package = sf)
            c.getter

    @pytest.mark.parametrize(('sf', 'expected'), [
        ('spam', SetupPyMetadataExtractor),
        ('%s/test_data/restsh-0.1.tar.gz' % tests_dir, LocalMetadataExtractor)
    ])
    def test_get_metadata_extractor(self, sf, expected):
        c = Convertor(package = sf)
        c.local_file = 'spamfile'
        c.name = 'spam'
        assert isinstance(c.metadata_extractor, expected)
