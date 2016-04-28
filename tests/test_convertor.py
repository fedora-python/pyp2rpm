import pytest

from flexmock import flexmock

from pyp2rpm.convertor import Convertor
from pyp2rpm.exceptions import *
from pyp2rpm.metadata_extractors import *
from pyp2rpm.package_getters import *
from pyp2rpm import settings

tests_dir = os.path.split(os.path.abspath(__file__))[0]
settings.CONSOLE_LOGGING = True


class TestConvertor(object):
    td_dir = '{0}/test_data/'.format(tests_dir)
    client = flexmock(package_releases=lambda n: n == 'spam' and ['0.1'] or [])
    Convertor._client = client  # flexmock can't mock properties yet

    @pytest.mark.parametrize(('sf', 'g'), [
        ('spam', PypiDownloader),
        ('{0}restsh-0.1.tar.gz'.format(td_dir), LocalFileGetter)
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
            c = Convertor(package=sf)
            c.getter

    @pytest.mark.parametrize(('sf', 'expected'), [
        ('{0}plumbum-0.9.0.tar.gz'.format(td_dir), DistMetadataExtractor),
        ('{0}setuptools-19.6-py2.py3-none-any.whl'.format(td_dir), WheelMetadataExtractor)
    ])
    def test_get_metadata_extractor(self, sf, expected):
        c = Convertor(package=sf)
        c.local_file = sf
        c.name = 'plumbum'
        assert isinstance(c.metadata_extractor, expected)
