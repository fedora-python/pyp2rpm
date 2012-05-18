import os
import tempfile

import pytest

from pyp2rpmlib.package_getters import *

tests_dir = os.path.split(os.path.abspath(__file__))[0]

class TestLocalFileGetter(object):
    td_dir = '%s/test_data/' % tests_dir

    def setup_method(self, method):
        self.l = [LocalFileGetter('%splumbum-0.9.0.tar.gz' % self.td_dir),
                  LocalFileGetter('%sSphinx-1.1.3-py2.6.egg' % self.td_dir),
                  LocalFileGetter('%sunextractable-1.tar' % self.td_dir),
                 ]

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, 'plumbum-0.9.0'),
        (1, 'Sphinx-1.1.3-py2.6'),
        (2, 'unextractable-1'),
    ])
    def test__stripped_name_version(self, i, expected):
        assert self.l[i]._stripped_name_version == expected

    @pytest.mark.parametrize(('i', 'expected'), [
        (0, ('plumbum', '0.9.0')),
        (1, ('Sphinx', '1.1.3')),
        (2, ('unextractable', '1')),
    ])
    def test_stripped_name_version(self, i, expected):
        assert self.l[i].get_name_version() == expected

    def test_get_non_existent_file(self):
        with pytest.raises(EnvironmentError):
            LocalFileGetter('/this/path/doesnot/exist', tempfile.gettempdir()).get()

    def test_get_existent_file(self):
        tmpdir = tempfile.gettempdir()
        in_tmp_dir = os.path.join(tmpdir, 'plumbum-0.9.0.tar.gz')
        self.l[0].save_dir = tmpdir
        if os.path.exists(in_tmp_dir):
            os.unlink(in_tmp_dir)
        assert self.l[0].get() == in_tmp_dir
        assert os.path.exists(self.l[0].get())
        os.unlink(in_tmp_dir)

    def test_get_to_same_location(self):
        tmpdir = tempfile.gettempdir()
        self.l[1].save_dir = self.td_dir
        assert os.path.samefile(self.l[1].get(), os.path.join(self.td_dir, 'Sphinx-1.1.3-py2.6.egg'))
        assert not os.path.exists(os.path.join(tmpdir, 'Sphinx-1.1.3-py2.6.egg'))
