import pytest

from pyp2rpm.name_convertor import NameConvertor, DandifiedNameConvertor, NameVariants
from pyp2rpm import settings

try:
    import dnf
except ImportError:
    dnf = None


class TestUtils(object):

    def setup_method(self, method):
        self.ncf = NameConvertor('fedora')
        self.ncm = NameConvertor('mageia')

    @pytest.mark.parametrize(('input', 'expected_f', 'expected_m'), [
        ('python-spam', 'python-spam', 'python-spam'),
        ('python-PySpam', 'python-PySpam', 'python-pyspam'),
        ('python-spampy', 'python-spampy', 'python-spampy'),
        ('spam-python', 'python-spam', 'python-spam'),
        ('python26-foo', 'python-foo', 'python-foo'),
        ('foo-python26', 'python-foo', 'python-foo'),
        ('python3-foo', 'python-foo', 'python-foo'),
        ('foo-python3', 'python-foo', 'python-foo'),
    ])
    def test_rpm_name(self, input, expected_f, expected_m):
        assert self.ncf.rpm_name(input) == expected_f
        assert self.ncm.rpm_name(input) == expected_m

    @pytest.mark.parametrize(('name', 'version', 'expected'), [
        ('python-spam', None, 'python-spam'),
        ('pyspam', None, 'pyspam'),
        ('python-spam', '3', 'python3-spam'),
        ('pyspam', '26', 'python26-pyspam'),
        ('pyspam', settings.DEFAULT_PYTHON_VERSION, 'pyspam'),
        ('python-foo', '26', 'python26-foo'),
        ('python-foo', '3', 'python3-foo'),
        ('python2-foo', None, 'python-foo'),
        ('python2-foo', '3', 'python3-foo'),
        ('python26-foo', '3', 'python3-foo'),
        ('python26-foo', None, 'python-foo'),
        ('python-foo', '25', 'python25-foo'),
        ('python2-devel', 3, 'python3-devel'),
        ('python2-devel', None, 'python2-devel'),
    ])
    def test_rpm_versioned_name(self, name, version, expected):
        assert NameConvertor.rpm_versioned_name(name, version) == expected


class TestDandifiedNameConvertor(object):

    def setup_method(self, method):
        self.dnc = DandifiedNameConvertor('fedora')

    @pytest.mark.parametrize(('pypi_name', 'version', 'expected'), [
        ('Babel', '2', 'python2-babel'),
        ('Babel', '3', 'python3-babel'),
        ('MarkupSafe', '2', 'python-markupsafe'),
        ('MarkupSafe', '3', 'python3-markupsafe'),
        ('Jinja2', '2', 'python-jinja2'),
        ('Jinja2', '3', 'python3-jinja2'),
        ('Sphinx', '2', 'python2-sphinx'),
        ('Sphinx', '3', 'python3-sphinx'),
        ('Cython', '2', 'Cython'),
        ('Cython', '3', 'python3-Cython'),
        ('pytest', '2', 'python2-pytest'),
        ('pytest', '3', 'python3-pytest'),
        ('vertica', '2', 'vertica-python'),
        ('pycairo', '2', 'pycairo'),
        ('pycairo', '3', 'python3-cairo'),
        ('oslosphinx', '2', 'python2-oslo-sphinx'),
        ('oslosphinx', '3', 'python3-oslo-sphinx'),
        ('mock', '2', 'python2-mock'),
        ('mock', '3', 'python3-mock'),
    ])
    @pytest.mark.skipif(dnf is None, reason="Optional dependency DNF required")
    def test_rpm_name(self, pypi_name, version, expected):
        assert self.dnc.rpm_name(pypi_name, version) == expected


class TestNameVariants(object):

    def setup_method(self, method):
        self.nv = NameVariants('foo', '3')
        self.mv = NameVariants('foo', '')

    @pytest.mark.parametrize(('version', 'input_list', 'expected'), [
        ('3', ['python3-Foo', 'foo-python', 'python-foo'], 'python3-Foo'),
        ('', ['python3-Foo', 'foo-python', 'python-foo'], 'python-foo'),
        ('2', ['python3-Foo', 'foo-python', 'foo'], 'foo'),
    ])
    def test_best_matching(self, version, input_list, expected):
        self.nv.version = version
        self.nv.names_init()
        self.nv.variants_init()
        for name in input_list:
            self.nv.find_match(name)
        assert self.nv.best_matching == expected

    @pytest.mark.parametrize(('first_list', 'second_list', 'expected'), [
        (['python3-foo', 'py3foo'], ['foo', 'python-foo'], {'python_ver_name': 'python3-foo',
                                                            'pyver_name': 'py3foo',
                                                            'name_python_ver': None,
                                                            'raw_name': 'foo'})

    ])
    def test_merge(self, first_list, second_list, expected):
        for first, second in zip(first_list, second_list):
            self.nv.find_match(first)
            self.mv.find_match(second)
        assert self.nv.merge(self.mv).variants == expected
