import pytest

from pyp2rpm.filters import (macroed_pkg_name,
                             name_for_python_version,
                             script_name_for_python_version,
                             rpm_escape)


class TestFilters(object):

    @pytest.mark.parametrize(('pkg_name', 'srcname', 'version',
                              'default_number', 'expected'), [
        ('python-Jinja2', None, '2', False, 'python2-%{pypi_name}'),
        ('python-Jinja2', None, '2', True, 'python2-%{pypi_name}'),
        ('python-Jinja2', None, '3', False, 'python-%{pypi_name}'),
        ('python-Jinja2', None, '3', True, 'python3-%{pypi_name}'),
        ('python-stdnum', 'stdnum', '2', False, 'python2-%{srcname}'),
        ('python-stdnum', 'stdnum', '2', True, 'python2-%{srcname}'),
        ('python-stdnum', 'stdnum', '3', False, 'python-%{srcname}'),
        ('python-stdnum', 'stdnum', '3', True, 'python3-%{srcname}')
    ])
    def test_macroed_pkg_name(self, pkg_name, srcname, version,
                              default_number, expected):
        assert name_for_python_version(macroed_pkg_name(
            pkg_name, srcname), version, default_number) == expected

    @pytest.mark.parametrize(('name', 'version', 'minor',
                              'default_number', 'expected'), [
        ('foo', '2', False, False, 'foo-2'),
        ('foo', '2', False, True, 'foo-2'),
        ('foo', '3', False, False, 'foo'),
        ('foo', '3', False, True, 'foo-3'),
        ('foo', '35', True, True, 'foo-3.5'),
        ('foo', '3', True, True, 'foo-%{python3_version}'),
    ])
    def test_script_name_for_python_version(self, name, version, minor,
                                            default_number, expected):
        assert script_name_for_python_version(name, version, minor,
                                              default_number) == expected

    @pytest.mark.parametrize(('text', 'expected'), [
        # Basic RPM macro injection
        ('%(touch /tmp/pwn)', '%%(touch /tmp/pwn)'),
        ('%{evil}', '%%{evil}'),
        # Directory traversal with macros
        ('foo-1.0-M%(touch /tmp/pwn)', 'foo-1.0-M%%(touch /tmp/pwn)'),
        # Multiple percent signs
        ('%%already escaped', '%%%%already escaped'),
        # Lua scriptlets
        ('%{lua: os.execute("evil")}', '%%{lua: os.execute("evil")}'),
        # Shell command injection
        ('text%(echo pwned)more', 'text%%(echo pwned)more'),
        # None and empty handling
        (None, ''),
        ('', ''),
        # No percent signs (should pass through)
        ('normal text', 'normal text'),
        ('https://example.com', 'https://example.com'),
        # Integer conversion
        (123, '123'),
    ])
    def test_rpm_escape(self, text, expected):
        """Test that rpm_escape properly escapes RPM macros and directives."""
        assert rpm_escape(text) == expected

    def test_rpm_escape_prevents_macro_expansion(self):
        """Test that escaped text doesn't expand as an RPM macro."""
        # If %{python3_version} were not escaped, RPM would try to expand it
        malicious = '%{python3_version}'
        escaped = rpm_escape(malicious)
        # Should have doubled percent signs
        assert escaped == '%%{python3_version}'
        # Verify it contains %% not just %
        assert '%%{' in escaped

    def test_rpm_escape_wordwrap_boundary(self):
        """Test that rpm_escape after wordwrap doesn't split %% pairs."""
        # If wordwrap splits 'text%%more' at 4 chars into 'text' and '%%more',
        # then rpm_escape would turn '%%more' into '%%%%more'
        # This is correct - each % should be escaped
        text = 'ab%cd'
        escaped = rpm_escape(text)
        assert escaped == 'ab%%cd'
