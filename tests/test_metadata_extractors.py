import os

from tarfile import TarFile
from zipfile import ZipFile

import pytest

from flexmock import flexmock

from pyp2rpmlib.archive import Archive
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
                  MetadataExtractor('%sversiontools-1.9.1.tar.gz' % self.td_dir, 'versiontools', '1.9.1'),
                 ]

    def test_runtime_deps_from_egg_info_no_deps(self):
        flexmock(Archive).should_receive('get_content_of_file').with_args('EGG-INFO/requires.txt', True).and_return('')
        assert self.e[3].runtime_deps_from_egg_info == []

    def test_runtime_deps_from_egg_info_some_deps(self):
        flexmock(Archive).should_receive('get_content_of_file').with_args('EGG-INFO/requires.txt', True).and_return('spam>1.0\n\n')
        assert len(self.e[3].runtime_deps_from_egg_info) == 1

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, True),
        (1, True),
        (3, False),
        (4, False),
    ])
    def test_has_bundled_egg_info(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].has_bundled_egg_info == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, False),
        (3, False),
        (4, False),
        (5, True),
    ])
    def test_has_extension(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].has_extension == expected
    @pytest.mark.parametrize(('i', 'expected'), [
        (0, ['README.rst', 'LICENSE']),
        (1, ['README.txt', 'LICENSE']),
        (3, []),
    ])
    def test_doc_files(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].doc_files == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, None),
        (6, 'versiontools-1.9.1/doc'),
    ])
    def test_sphinx_dir(self, i, expected):
        with self.e[i].archive:
            assert self.e[i].sphinx_dir == expected

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

class TestLocalMetadataExtractor(object):
    td_dir = '%s/test_data/' % tests_dir

    def setup_method(self, method): # test for non-egg and egg
        self.e = [LocalMetadataExtractor('%splumbum-0.9.0.tar.gz' % self.td_dir, 'plumbum', '0.9.0'),
                  LocalMetadataExtractor('%sSphinx-1.1.3-py2.6.egg' % self.td_dir, 'Sphinx', '1.1.3')
                 ]

    @pytest.mark.parametrize(('i', 'what', 'expected'), [
        (0, 'description', 'TODO:'), # try random non-set attribute
        (0, 'license','MIT'),
        (1, 'license', 'BSD'),
    ])
    def test_extract(self, i, what, expected):
        data = self.e[i].extract_data()
        assert getattr(data, what) == expected
