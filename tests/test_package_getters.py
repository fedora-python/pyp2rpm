import os

import pytest

from pyp2rpmlib.package_getters import *

tests_dir = os.path.split(os.path.abspath(__file__))[0]

class TestLocalFileGetter(object):
    td_dir = '%s/test_data/' % tests_dir

    def setup_method(self, method):
        self.l = [LocalFileGetter('%splumbum-0.9.0.tar.gz' % self.td_dir),
                  LocalFileGetter('%sSphynx-1.1.3-py2.6.egg' % self.td_dir),
                  LocalFileGetter('%sunextractable-1.tar' % self.td_dir),
                 ]

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, 'plumbum-0.9.0'),
        (1, 'Sphynx-1.1.3-py2.6'),
        (2, 'unextractable-1'),
    ])
    def test__stripped_name_version(self, i, expected):
        assert self.l[i]._stripped_name_version == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, ('plumbum', '0.9.0')),
        (1, ('Sphynx', '1.1.3')),
        (2, ('unextractable', '1')),
    ])
    def test__stripped_name_version(self, i, expected):
        assert self.l[i].get_name_version() == expected
