import pytest
import os

from flexmock import flexmock

from pyp2rpm.convertor import Convertor
from pyp2rpm.exceptions import NoSuchPackageException
from pyp2rpm.metadata_extractors import (SetupPyMetadataExtractor,
                                         WheelMetadataExtractor)
from pyp2rpm.package_getters import PypiDownloader, LocalFileGetter
from pyp2rpm.package_data import PackageData

tests_dir = os.path.split(os.path.abspath(__file__))[0]


class TestConvertor(object):
    td_dir = '{0}/test_data/'.format(tests_dir)
    client = flexmock(package_releases=lambda n, hidden: n == 'spam' and ['0.1'] or [])
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
        ('{0}plumbum-0.9.0.tar.gz'.format(td_dir), SetupPyMetadataExtractor),
        ('{0}setuptools-19.6-py2.py3-none-any.whl'.format(td_dir),
         WheelMetadataExtractor)
    ])
    def test_get_metadata_extractor(self, sf, expected):
        c = Convertor(package=sf)
        c.local_file = sf
        c.name = 'plumbum'
        assert isinstance(c.metadata_extractor, expected)

    @pytest.mark.parametrize(('self_bv', 'self_pv', 'data_pv',
                              'expected_bv', 'expected_pv'), [
        (None, [], ['2', '3'], '3', []),
        (None, [], ['3', '2'], '3', []),
        (None, [], [], '3', []),
        (None, ['2'], [], '3', ['2']),
        (None, ['2'], ['2'], '2', []),
        (None, ['2'], ['3'], '3', ['2']),
        ('2', [], ['2', '3'], '2', []),
        ('3', [], ['3', '2'], '3', []),
        ('3', ['2'], ['2', '3'], '3', ['2']),
    ])
    def test_merge_versions_fedora(self, self_bv, self_pv, data_pv,
                                   expected_bv, expected_pv):
        c = Convertor(package='pkg', base_python_version=self_bv,
                      python_versions=self_pv, template='fedora.spec')
        data = PackageData('pkg.tar.gz', 'pkg', 'pkg', '0.1')
        data.python_versions = data_pv
        c.merge_versions(data)
        assert data.base_python_version == expected_bv
        assert data.python_versions == expected_pv

    @pytest.mark.parametrize(('self_bv', 'self_pv', 'data_bv', 'data_pv',
                              'expected_bv', 'expected_pv'), [
        (None, [], '2', ['3'], '2', []),
        (None, ['2'], '2', [], '2', []),
        ('2', [], '2', ['2'], '2', []),
        ('2', '2', '2', ['2'], '2', []),
    ])
    def test_merge_versions_epel6(self, self_bv, self_pv, data_bv, data_pv,
                                  expected_bv, expected_pv):
        c = Convertor(package='pkg', base_python_version=self_bv,
                      python_versions=self_pv, template='epel6.spec',
                      distro='epel6')
        data = PackageData('pkg.tar.gz', 'pkg', 'pkg', '0.1')
        data.base_python_version = data_bv
        data.python_versions = data_pv
        c.merge_versions(data)
        assert data.base_python_version == expected_bv
        assert data.python_versions == expected_pv

    @pytest.mark.parametrize(('self_bv', 'self_pv', 'data_pv',
                              'expected_bv', 'expected_pv'), [
        (None, [], ['2', '3'], '2', ['3']),
        (None, [], ['3', '2'], '2', ['3']),
        (None, [], [], '2', ['3']),
        (None, ['2'], [], '2', []),
        (None, ['2'], ['2'], '2', []),
        (None, ['2'], ['3'], '3', ['2']),
        ('2', [], ['2', '3'], '2', ['3']),
        ('3', [], ['3', '2'], '3', []),
        ('3', ['2'], ['2', '3'], '3', ['2']),
    ])
    def test_merge_versions_epel7(self, self_bv, self_pv, data_pv,
                                  expected_bv, expected_pv):
        c = Convertor(package='pkg', base_python_version=self_bv,
                      python_versions=self_pv, template='epel7.spec',
                      distro='epel7')
        data = PackageData('pkg.tar.gz', 'pkg', 'pkg', '0.1')
        data.python_versions = data_pv
        c.merge_versions(data)
        assert data.base_python_version == expected_bv
        assert data.python_versions == expected_pv

    @pytest.mark.parametrize(('self_bv', 'self_pv'), [
        ('3', []),
        (None, ['3']),
        ('3', ['3'])
    ])
    def test_bad_versions(self, self_bv, self_pv):
        c = Convertor(package='pkg', base_python_version=self_bv,
                      python_versions=self_pv, template='epel6.spec',
                      distro='epel6')
        data = PackageData('pkg.tar.gz', 'pkg', 'pkg', '0.1')
        with pytest.raises(SystemExit):
            c.merge_versions(data)
