{{ data.credit_line }}
{% from 'macros.spec' import dependencies, for_python_versions, underscored_or_pypi -%}
%global pypi_name {{ data.name }}

Name:           {{ data.pkg_name|macroed_pkg_name(data.name) }}
Version:        {{ data.version }}
Release:        1%{?dist}
Summary:        {{ data.summary }}

License:        {{ data.license }}
URL:            {{ data.home_page }}
Source0:        {{ data.url|replace(data.name, '%{pypi_name}')|replace(data.version, '%{version}') }}

{%- if not data.has_extension %}
BuildArch:      noarch
{%- endif %}
{{ dependencies(data.build_deps, False, data.base_python_version, data.base_python_version,
use_with=True, epel=True) }}
{%- for pv in data.python_versions %}
{{ dependencies(data.build_deps, False, pv, data.base_python_version,
use_with=False, epel=True) }}
{%- endfor %}

%description
{{ data.description|truncate(400)|wordwrap }}
{% for pv in ([data.base_python_version] + data.python_versions) %}
%package -n     {{data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv, True, True)}}
Summary:        {{ data.summary }}
{{ dependencies(data.runtime_deps, True, pv, pv, use_with=False, epel=True) }}
%description -n {{data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv, True, True)}}
{{ data.description|truncate(400)|wordwrap }}
{% endfor -%}
{%- if data.sphinx_dir %}
%package -n python-%{pypi_name}-doc
Summary:        {{ data.name }} documentation
%description -n python-%{pypi_name}-doc
Documentation for {{ data.name }}
{%- endif %}

%prep
%autosetup -n %{pypi_name}-%{version}
{%- if data.has_bundled_egg_info %}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
{%- endif %}

%build
{%- for pv in [data.base_python_version] + data.python_versions %}
{% if data.has_extension %}CFLAGS="$RPM_OPT_FLAGS" {% endif %}{{'%{__python2}'|python_bin_for_python_version(pv) }} setup.py build
{%- endfor %}
{%- if data.sphinx_dir %}
# generate html docs 
{{ "sphinx-build"|script_name_for_python_version(data.base_python_version, False, False) }} {{ data.sphinx_dir }} html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}
{%- endif %}

%install
{%- if data.python_versions|length > 0 %}
# Must do the subpackages' install first because the scripts in /usr/bin are
# overwritten with every setup.py install.
{%- endif %}
{%- for pv in data.python_versions + [data.base_python_version] %}
{{ '%{__python2}'|python_bin_for_python_version(pv) }} setup.py install --skip-build --root %{buildroot}
{% for script in data.scripts -%}
cp %{buildroot}/%{_bindir}/{{ script }} %{buildroot}/%{_bindir}/{{ script|script_name_for_python_version(pv) }}
ln -sf %{_bindir}/{{ script|script_name_for_python_version(pv) }} %{buildroot}/%{_bindir}/{{ script|script_name_for_python_version(pv, True) }}
{% endfor %}
{%- endfor -%}
{% if data.has_test_suite %}

%check
{%- for pv in [data.base_python_version] + data.python_versions %}
%{__python{{ pv }}} setup.py test
{%- endfor %}
{%- endif %}
{% for pv in [data.base_python_version] + data.python_versions %}
%files -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv, True, True) }} 
%doc {{data.doc_files|join(' ') }}
{%- for script in data.scripts %}
{%- if pv == data.base_python_version %}
%{_bindir}/{{ script }}
{%- endif %}
%{_bindir}/{{ script|script_name_for_python_version(pv) }}
%{_bindir}/{{ script|script_name_for_python_version(pv, True) }}
{%- endfor %}
{%- if data.py_modules %}
{% for module in data.py_modules -%}
{%- if pv == '3' -%}
%dir {{ '%{python2_sitelib}'|sitedir_for_python_version(pv) }}/__pycache__/
{{ '%{python2_sitelib}'|sitedir_for_python_version(pv) }}/__pycache__/*
{%- endif %}
{{ '%{python2_sitelib}'|sitedir_for_python_version(pv) }}/{{ data.name | module_to_path(module) }}.py{% if pv != '3'%}*{% endif %}
{%- endfor %}
{%- endif %}
{%- if data.has_extension %}
{{ '%{python2_sitearch}'|sitedir_for_python_version(pv) }}/{{ data.name | module_to_path(data.underscored_name) }}
{%- if data.has_pth %}
{{ '%{python2_sitearch}'|sitedir_for_python_version(pv) }}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py?.?-*.pth
{%- endif %}
{{ '%{python2_sitearch}'|sitedir_for_python_version(pv) }}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py?.?.egg-info
{%- else %}
{%- if data.has_packages %}
{%- for package in data.packages %}
{{ '%{python2_sitelib}'|sitedir_for_python_version(pv) }}/{{ package | package_to_path(data.underscored_name) }}
{%- endfor %}
{%- endif %}
{%- if data.has_pth %}
{{ '%{python2_sitelib}'|sitedir_for_python_version(pv) }}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py?.?-*.pth
{%- endif %}
{{ '%{python2_sitelib}'|sitedir_for_python_version(pv) }}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py?.?.egg-info
{%- endif %}
{% endfor %}
{%- if data.sphinx_dir %}
%files -n python-%{pypi_name}-doc
%doc html 
{% endif %}
%changelog
* {{ data.changelog_date_packager }} - {{ data.version }}-1
- Initial package.
