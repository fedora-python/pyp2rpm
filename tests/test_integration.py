import pytest
import os
from scripttest import TestFileEnvironment

tests_dir = os.path.split(os.path.abspath(__file__))[0]


class TestSpec(object):
    td_dir = '{0}/test_data/'.format(tests_dir)
    bin_dir = os.path.split(tests_dir)[0] + '/'
    exe = 'python {0}mybin.py'.format(bin_dir)

    def setup_method(self, method):
        self.env = TestFileEnvironment('{0}/test_output/'.format(tests_dir))

    @pytest.mark.parametrize(('package', 'options', 'expected'), [
        ('Jinja2', '-v2.8', 'python-Jinja2.spec'),
        ('Jinja2', '-v2.8 -b3', 'python-Jinja2_base.spec'),
        ('Jinja2', '-v2.8 -t epel7', 'python-Jinja2_epel7.spec'),
        ('Jinja2', '-v2.8 -t epel6', 'python-Jinja2_epel6.spec'),
        ('buildkit', '-v0.2.2 -b2', 'python-buildkit.spec'),
        ('StructArray', '-v0.1 -b2', 'python-StructArray.spec'),
        ('Sphinx', '-v1.5 -r python-sphinx', 'python-sphinx.spec'),
    ])
    @pytest.mark.spectest
    def test_spec(self, package, options, expected):
        with open(self.td_dir + expected) as fi:
            self.spec_content = fi.read()
        res = self.env.run('{0} {1} {2}'.format(self.exe, package, options))
        # changelog have to be cut from spec files
        assert set(res.stdout.split('\n')[1:-4]) == set(self.spec_content.split('\n')[1:-4])


class TestSrpm(object):
    td_dir = '{0}/test_data/'.format(tests_dir)
    bin_dir = os.path.split(tests_dir)[0] + '/'
    exe = 'python {0}mybin.py'.format(bin_dir)

    def setup_method(self, method):
        self.env = TestFileEnvironment('{0}/test_output/'.format(tests_dir))

    def test_srpm(self):
        res = self.env.run('{0} Jinja2 --srpm'.format(self.exe), expect_stderr=True)
        assert res.returncode == 0
