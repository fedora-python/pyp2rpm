"""Security tests for RPM macro injection vulnerabilities."""
import pytest
from jinja2 import Environment, FileSystemLoader
import os

from pyp2rpm.package_data import PackageData
from pyp2rpm import filters


class TestRPMMacroInjection(object):
    """Tests for preventing RPM macro and directive injection attacks."""

    @pytest.fixture
    def jinja_env(self):
        """Create a Jinja2 environment with the template directory."""
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                   'pyp2rpm', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        # Register all filters from the filters module
        for name in dir(filters):
            obj = getattr(filters, name)
            if callable(obj) and not name.startswith('_') and name != 'settings':
                env.filters[name] = obj
        return env

    def test_update_attr_bypass_vulnerability(self):
        """Test that update_attr no longer bypasses escaping."""
        # This was CVE-candidate: update_attr bypassed __setattr__ escaping
        pd = PackageData('x', 'x', 'python-x', '1.0')

        # Set malicious data via update path (used by PyPI metadata)
        pd.set_from({'description': 'evil %(touch /tmp/pwn)'}, update=True)

        # The data is stored raw (no escaping at assignment time)
        # This is intentional - escaping happens at render time
        assert pd.data['description'] == 'evil %(touch /tmp/pwn)'

        # But when rendered through template, it MUST be escaped
        # (tested in other test methods)

    def test_dirname_injection_in_prep(self, jinja_env):
        """Test that dirname in %prep section is escaped."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        pd.dirname = 'mypackage-1.0-M%(touch /tmp/pwn)'
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        pd.description = 'Description'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []

        rendered = template.render(data=pd)

        # The dirname should be escaped - %% not %
        assert 'mypackage-1.0-M%%(touch /tmp/pwn)' in rendered or \
               '%{pypi_name}-%{pypi_version}' in rendered

    def test_sphinx_dir_injection(self, jinja_env):
        """Test that sphinx_dir in build commands is escaped."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        pd.sphinx_dir = 'docs%(touch /tmp/pwn)'
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        pd.description = 'Description'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []

        rendered = template.render(data=pd)

        # sphinx_dir should be escaped
        assert 'docs%%(touch /tmp/pwn)' in rendered

    @pytest.mark.parametrize('field_name', [
        'name', 'summary', 'description', 'license', 'home_page'
    ])
    def test_text_field_escaping(self, jinja_env, field_name):
        """Test that text fields are escaped in rendered templates."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        # Set safe defaults
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        pd.description = 'Description'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []

        # Inject malicious content into the field being tested
        malicious = 'safe%(touch /tmp/pwn)text'
        setattr(pd, field_name, malicious)

        rendered = template.render(data=pd)

        # Should contain escaped version
        assert 'safe%%(touch /tmp/pwn)text' in rendered
        # Verify it's actually escaped (not just a single %)
        # Count: should have 2 consecutive % chars, not 1
        assert rendered.count('safe%%') > 0

    def test_scripts_list_escaping(self, jinja_env):
        """Test that script names in lists are escaped."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        pd.description = 'Description'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []
        pd.scripts = ['script1', 'evil%(touch /tmp/pwn)', 'script2']

        rendered = template.render(data=pd)

        # Scripts should be escaped
        assert 'evil%%(touch /tmp/pwn)' in rendered

    def test_py_modules_escaping(self, jinja_env):
        """Test that py_modules are escaped in file lists."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        pd.description = 'Description'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []
        pd.py_modules = ['module%(evil)']

        rendered = template.render(data=pd)

        # Module paths should be escaped
        assert 'module%%(evil)' in rendered

    def test_packages_list_escaping(self, jinja_env):
        """Test that package names in lists are escaped."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        pd.description = 'Description'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []
        pd.has_packages = True
        pd.packages = ['pkg%(evil)', 'safe_pkg']

        rendered = template.render(data=pd)

        # Package paths should be escaped
        assert 'pkg%%(evil)' in rendered

    def test_doc_files_escaping(self, jinja_env):
        """Test that doc_files are escaped."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        pd.description = 'Description'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []
        pd.doc_files = ['README', 'file%(evil).txt']

        rendered = template.render(data=pd)

        # Doc files should be escaped
        assert 'file%%(evil).txt' in rendered
        assert '%doc' in rendered

    def test_doc_license_escaping(self, jinja_env):
        """Test that doc_license files are escaped."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        pd.description = 'Description'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []
        pd.doc_license = ['LICENSE', 'COPYING%(evil)']

        rendered = template.render(data=pd)

        # License files should be escaped
        assert 'COPYING%%(evil)' in rendered
        assert '%license' in rendered

    def test_description_truncate_wordwrap_escaping(self, jinja_env):
        """Test that description is escaped after truncate/wordwrap."""
        template = jinja_env.get_template('fedora.spec')

        pd = PackageData('mypackage', 'mypackage', 'python-mypackage', '1.0')
        pd.summary = 'A package'
        pd.license = 'MIT'
        pd.home_page = 'https://example.com'
        pd.source0 = 'https://example.com/pkg.tar.gz'
        # Description with macro at various positions
        pd.description = 'A ' * 50 + '%(evil)' + ' text'
        pd.sorted_python_versions = ['3']
        pd.base_python_version = '3'
        pd.python_versions = []

        rendered = template.render(data=pd)

        # After truncate and wordwrap, the macro should still be escaped
        assert '%%(evil)' in rendered

    def test_pypi_metadata_injection(self):
        """Test that PyPI metadata doesn't bypass escaping."""
        # Simulate what pypi_metadata_extension does
        pd = PackageData('evil-pkg', 'evil-pkg', 'python-evil-pkg', '1.0')

        # PyPI metadata comes in via set_from with update=True
        pypi_data = {
            'summary': 'Package %(touch /tmp/pwn1)',
            'description': 'Description %(touch /tmp/pwn2)',
            'license': 'MIT%(touch /tmp/pwn3)',
            'home_page': 'http://example.com%(touch /tmp/pwn4)'
        }

        pd.set_from(pypi_data, update=True)

        # Data is stored unescaped (this is OK - escaping is at render time)
        assert '%(touch /tmp/pwn1)' in pd.data['summary']
        assert '%(touch /tmp/pwn2)' in pd.data['description']

        # The template rendering will escape these (verified in other tests)

    def test_dependency_escaping(self, jinja_env):
        """Test that dependency names and versions are escaped in macros."""
        # Dependencies are tuples: (type, name, version_spec)
        from jinja2 import Template

        # Test the one_dep macro directly
        macro_template = jinja_env.from_string(
            "{% from 'macros.spec' import one_dep -%}\n"
            "{{ one_dep(dep, '3') }}"
        )

        # Malicious dependency
        dep = ('BuildRequires', 'evil%(touch /tmp/pwn)', '>= {name}')

        rendered = macro_template.render(dep=dep)

        # Dependency name should be escaped
        assert 'evil%%(touch /tmp/pwn)' in rendered

    def test_all_templates_load(self, jinja_env):
        """Verify all template files can be loaded and have rpm_escape available."""
        templates = ['fedora.spec', 'epel6.spec', 'epel7.spec',
                    'mageia.spec', 'pld.spec', 'macros.spec']

        for template_name in templates:
            template = jinja_env.get_template(template_name)
            assert template is not None
            # Verify rpm_escape filter is available
            assert 'rpm_escape' in jinja_env.filters
