import os
import xmlrpclib

from tarfile import TarFile
from zipfile import ZipFile

import pytest

from flexmock import flexmock

from pyp2rpmlib.metadata_extractors import *
from pyp2rpmlib import settings

tests_dir = os.path.split(os.path.abspath(__file__))[0]

class TestMetadataExtractor(object):
    td_dir = '%s/test_data/' % tests_dir

    def setup_method(self, method):
        # create fresh extractors for every test

        self.e = [MetadataExtractor('%splumbum-0.9.0.tar.gz' % self.td_dir, 'plumbum', '0.9.0'),
                  MetadataExtractor('%spytest-2.2.3.zip' % self.td_dir, 'pytest', '2.2.3'),
                  MetadataExtractor('%srestsh-0.1.tar.gz' % self.td_dir, 'restsh', '0.1'),
                  MetadataExtractor('%sSphinx-1.1.3-py2.6.egg' % self.td_dir, 'Sphinx', '1.1.3'),
                  MetadataExtractor('%sunextractable-1.tar' % self.td_dir, 'unextractable', '1'),
                  MetadataExtractor('%sbitarray-0.8.0.tar.gz' % self.td_dir, 'bitarray', '0.8.0'),
                 ]

    @pytest.mark.parametrize(('i', 's', 'expected'), [
        (0, '.gz',  TarFile),
        (1, '.zip', ZipFile),
        (2, '.gz', TarFile),
        (3, '.egg', ZipFile),
        (4, '.tar', TarFile),
    ])
    def test_get_extractor_cls(self, i, s, expected):
        assert self.e[i].get_extractor_cls(s) == expected

    @pytest.mark.parametrize(('i', 'n', 'expected'), [
        (0, 'setup.cfg', '[egg_info]\r\ntag_build = \r\ntag_date = 0\r\ntag_svn_revision = 0\r\n\r\n'),
        (1, 'requires.txt', 'py>=1.4.7.dev2'),
        (2, 'does_not_exist.dne', None),
        (4, 'in_unextractable', None),
    ])
    def test_get_content_of_file_from_archive(self, i, n, expected):
        assert self.e[i].get_content_of_file_from_archive(n) == expected

    def test_find_list_argument_not_present(self):
        flexmock(self.e[4]).should_receive('get_content_of_file_from_archive').with_args('setup.py').and_return('install_requires=["spam",\n"eggs"]')
        assert self.e[4].find_list_argument('setup_requires') == []

    def test_find_list_argument_present(self):
        flexmock(self.e[4]).should_receive('get_content_of_file_from_archive').with_args('setup.py').and_return('install_requires=["beans",\n"spam"]\nsetup_requires=["spam"]')
        assert self.e[4].find_list_argument('install_requires') == ['beans', 'spam']

    def test_find_list_argument_unopenable_file(self):
        flexmock(self.e[4]).should_receive('get_content_of_file_from_archive').with_args('setup.py').and_return(None)
        assert self.e[4].find_list_argument('install_requires') == []

    def test_runtime_deps_from_egg_info_no_deps(self):
        flexmock(self.e[3]).should_receive('get_content_of_file_from_archive').with_args('requires.txt').and_return('')
        assert self.e[3].runtime_deps_from_egg_info == []

    def test_runtime_deps_from_egg_info_some_deps(self):
        flexmock(self.e[3]).should_receive('get_content_of_file_from_archive').with_args('requires.txt').and_return('spam>1.0\n\n')
        assert len(self.e[3].runtime_deps_from_egg_info) == 1

    @pytest.mark.parametrize(('i', 'suf', 'expected'), [
        (0, ['.spamspamspam'],  False),
        (1, '.py', True),
        (4, ['.eggs'], False),
    ])
    def test_has_file_with_suffix(self, i, suf, expected):
        assert self.e[i].has_file_with_suffix(suf) == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, True),
        (1, True),
        (3, False),
        (4, False),
    ])
    def test_has_bundled_egg_info(self, i, expected):
        assert self.e[i].has_bundled_egg_info == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, False),
        (3, False),
        (4, False),
        (5, True),
    ])
    def test_has_extension(self, i, expected):
        assert self.e[i].has_extension == expected


class TestPypiMetadataExtractor(object):
    td_dir = '%s/test_data/' % tests_dir
    client = flexmock(
        release_urls = lambda n, v: [{'md5_digest': '9a7a2f6943baba054cf1c28e05a9198e',
                                      'url': 'http://pypi.python.org/packages/source/r/restsh/restsh-0.1.tar.gz'}],
        release_data = lambda n, v: {'description': 'UNKNOWN',
                                     'release_url': 'http://pypi.python.org/pypi/restsh/0.1',
                                     'classifiers': ['Development Status :: 4 - Beta',
                                                     'Intended Audience :: Developers',
                                                     'License :: OSI Approved :: BSD License',
                                                     'Operating System :: OS Independent'
                                                     ],
                                     'license': 'BSD',
                                     'summary': 'A simple rest shell client',
                                     'spam': 'eggs and beans'
                                    }
    )

    def setup_method(self, method):
        # we will only test getting stuff from the client => pass spam as file
        self.e = PypiMetadataExtractor('spam', 'restsh', '0.1', self.client)

    @pytest.mark.parametrize(('what', 'expected'), [
        ('description', 'UNKNOWN'),
        ('md5','9a7a2f6943baba054cf1c28e05a9198e'),
        ('url', 'http://pypi.python.org/packages/source/r/restsh/restsh-0.1.tar.gz'),
        ('license', 'BSD'),
        ('summary', 'A simple rest shell client')
    ])
    def test_extract(self, what, expected):
        data = self.e.extract_data()
        assert getattr(data, what) == expected
