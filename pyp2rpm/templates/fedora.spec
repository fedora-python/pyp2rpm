{{ data.credit_line }}
{% from 'macros.spec' import dependencies, for_python_versions, underscored_or_pypi, macroed_url -%}
%global pypi_name {{ data.name|rpm_escape }}
%global pypi_version {{ data.version|rpm_escape }}
{%- if data.srcname %}
%global srcname {{ data.srcname|rpm_escape }}
{%- endif %}

Name:           {{ data.pkg_name|macroed_pkg_name(data.srcname) }}
Version:        {{ data.version|rpm_version }}
Release:        1%{?dist}
Summary:        {{ data.summary|rpm_escape }}

License:        {{ data.license|rpm_escape }}
URL:            {{ data.home_page|rpm_escape }}
Source0:        {{ data.source0|rpm_escape|replace(data.name|rpm_escape, '%{pypi_name}')|replace(data.version|rpm_escape, '%{pypi_version}')|macroed_url }}

{%- if not data.has_extension %}
BuildArch:      noarch
{%- endif %}
{%- for pv in data.sorted_python_versions %}
{{ dependencies(data.build_deps, False, pv, data.base_python_version, False) }}
{%- endfor %}

%description
{{ data.description|truncate(400)|wordwrap|rpm_escape }}
{% for pv in data.sorted_python_versions %}
%package -n     {{data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(pv, True) }}
Summary:        %{summary}
%{?python_provide:%python_provide {{data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(pv, True)}}}
{{ dependencies(data.runtime_deps, True, pv, pv) }}
%description -n {{data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(pv, True) }}
{{ data.description|truncate(400)|wordwrap|rpm_escape }}
{% endfor -%}
{%- if data.sphinx_dir %}
%package -n {{ data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(None, True) }}-doc
Summary:        {{ data.name|rpm_escape }} documentation
%description -n {{ data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(None, True) }}-doc
Documentation for {{ data.name|rpm_escape }}
{%- endif %}

%prep
%autosetup -n {{ data.dirname|rpm_escape|replace(data.name|rpm_escape, '%{pypi_name}')|replace(data.version|rpm_escape, '%{pypi_version}')|default('%{pypi_name}-%{pypi_version}', true) }}
{%- if data.has_bundled_egg_info %}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
{%- endif %}

%build
{%- for pv in data.sorted_python_versions %}
%py{{ pv }}_build
{%- endfor %}
{%- if data.sphinx_dir %}
# generate html docs
PYTHONPATH=${PWD} {{ "sphinx-build"|script_name_for_python_version(data.base_python_version, False, True) }} {{ data.sphinx_dir|rpm_escape }} html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}
{%- endif %}

%install
{%- if data.python_versions|length > 0 %}
# Must do the default python version install last because
# the scripts in /usr/bin are overwritten with every setup.py install.
{%- endif %}
{%- for pv in data.python_versions + [data.base_python_version] %}
{%- if pv == data.base_python_version and data.python_versions and data.scripts %}
rm -rf %{buildroot}%{_bindir}/*
{%- endif %}
%py{{ pv }}_install
{%- endfor -%}
{% if data.has_test_suite %}

%check
{%- for pv in data.sorted_python_versions %}
%{__python{{ pv }}} setup.py test
{%- endfor %}
{%- endif %}
{% for pv in data.sorted_python_versions %}
%files -n {{ data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(pv, True) }}
{%- if data.doc_license %}
%license {{data.doc_license|map('rpm_escape')|join(' ')}}
{%- endif %}
{%- if data.doc_files %}
%doc {{data.doc_files|map('rpm_escape')|join(' ') }}
{%- endif %}
{%- if pv == data.base_python_version %}
{%- for script in data.scripts %}
%{_bindir}/{{ script|rpm_escape }}
{%- endfor %}
{%- endif %}
{%- if data.py_modules %}
{%- for module in data.py_modules -%}
{%- if pv == '3' %}
%{python{{ pv }}_sitelib}/__pycache__/*
{%- endif %}
%{python{{ pv }}_sitelib}/{{ data.name | module_to_path(module) }}.py{% if pv != '3'%}*{% endif %}
{%- endfor %}
{%- endif %}
{%- if data.has_extension %}
{%- if data.has_packages %}
{%- for package in data.packages %}
%{python{{ pv }}_sitearch}/{{ package | package_to_path(data.name) }}
{%- endfor %}
{%- endif %}
{%- if data.has_pth %}
%{python{{ pv }}_sitearch}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{pypi_version}-py%{python{{ pv }}_version}-*.pth
{%- endif %}
%{python{{ pv }}_sitearch}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{pypi_version}-py%{python{{ pv }}_version}.egg-info
{%- else %}
{%- if data.has_packages %}
{%- for package in data.packages %}
%{python{{ pv }}_sitelib}/{{ package | package_to_path(data.name) }}
{%- endfor %}
{%- endif %}
{%- if data.has_pth %}
%{python{{ pv }}_sitelib}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{pypi_version}-py%{python{{ pv }}_version}-*.pth
{%- endif %}
%{python{{ pv }}_sitelib}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{pypi_version}-py%{python{{ pv }}_version}.egg-info
{%- endif %}
{% endfor %}
{%- if data.sphinx_dir %}
%files -n {{ data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(None, True) }}-doc
%doc html
{%- if data.doc_license %}
%license {{data.doc_license|map('rpm_escape')|join(' ')}}
{%- endif %}
{% endif %}
%changelog
* {{ data.changelog_date_packager }} - {{ data.version|rpm_version(False) }}-1
- Initial package.
