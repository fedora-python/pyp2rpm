{{ data.credit_line }}
{% from 'macros.spec' import dependencies, for_python_versions, underscored_or_pypi -%}
%global pypi_name {{ data.name }}
{%- for pv in data.python_versions %}
%global with_python{{ pv }} 1
{%- endfor %}

Name:           {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(data.base_python_version) }}
Version:        {{ data.version }}
Release:        1%{?dist}
Summary:        {{ data.summary }}

License:        {{ data.license }}
URL:            {{ data.home_page }}
Source0:        {{ data.url|replace(data.name, '%{pypi_name}')|replace(data.version, '%{version}') }}

{%- if not data.has_extension %}
BuildArch:      noarch
{%- endif %}
{{ dependencies(data.build_deps, False, data.base_python_version, data.base_python_version) }}
{%- for pv in data.python_versions %}
{{ dependencies(data.build_deps, False, pv, data.base_python_version) }}
{%- endfor %}
{{ dependencies(data.runtime_deps, True, data.base_python_version, data.base_python_version) }}

%description
{{ data.description|truncate(400)|wordwrap }}
{% call(pv) for_python_versions(data.python_versions) -%}
%package -n     {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}
Summary:        {{ data.summary }}
{{ dependencies(data.runtime_deps, True, pv, pv) }}

%description -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}
{{ data.description|truncate(400)|wordwrap }}
{%- endcall %}

%prep
%setup -q -n %{pypi_name}-%{version}
{%- if data.has_bundled_egg_info %}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
{%- endif %}
{% call(pv) for_python_versions([data.base_python_version] + data.python_versions,
data.base_python_version) -%}
{%- if pv != data.base_python_version -%}
rm -rf python{{pv}}
cp -a . python{{pv}}
find python{{pv}} -name '*.py' | xargs sed -i '1s|^#!python|#!%{__python{{pv}}}|'
{%- endif %}
{%- if data.sphinx_dir %}
# generate html docs {# TODO: generate properly for other versions (pushd/popd into their dirs...)
# #}
sphinx-build{% if pv != data.base_python_version %}-{{ pv }}{% endif %} {{ data.sphinx_dir }} html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}
{%- endif %}
{%- endcall %}

%build
{%- call(pv) for_python_versions([data.base_python_version] + data.python_versions, data.base_python_version) -%}
{%- if pv != data.base_python_version -%}
pushd python{{ pv }}
{%- endif %}
{% if data.has_extension %}CFLAGS="$RPM_OPT_FLAGS" {% endif %}{{ '%{__python2}'|python_bin_for_python_version(pv) }} setup.py build
{% if pv != data.base_python_version -%}
popd
{%- endif %}
{%- endcall %}

%install
{%- if data.python_versions|length > 0 %}
# Must do the subpackages' install first because the scripts in /usr/bin are
# overwritten with every setup.py install (and we want the python2 version
# to be the default for now).
{%- endif -%}
{%- call(pv) for_python_versions(data.python_versions + [data.base_python_version], data.base_python_version) -%}
{%- if pv != data.base_python_version -%}
pushd python{{ pv }}
{%- endif %}
{{ '%{__python2}'|python_bin_for_python_version(pv) }} setup.py install --skip-build --root %{buildroot}
{%- if pv != data.base_python_version %}
{%- if data.scripts %}
{%- for script in data.scripts %}
mv %{buildroot}%{_bindir}/{{ script }} %{buildroot}/%{_bindir}/{{ script|script_name_for_python_version(pv) }}
{%- endfor %}
{%- endif %}
popd
{%- endif %}
{%- endcall %}

{%- if data.has_test_suite %}
%check
{%- call(pv) for_python_versions([data.base_python_version] + data.python_versions, data.base_python_version) -%}
{%- if pv != data.base_python_version -%}
pushd python{{ pv }}
{%- endif %}
{{ '%{__python2}'|python_bin_for_python_version(pv) }} setup.py test
{% if pv != data.base_python_version -%}
popd
{%- endif %}
{%- endcall %}
{%- endif %}

{% call(pv) for_python_versions([data.base_python_version] + data.python_versions, data.base_python_version) -%}
%files{% if pv != data.base_python_version %} -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}{% endif %}
%doc {% if data.sphinx_dir %}html {% endif %}{{ data.doc_files|join(' ') }}
{%- if data.scripts %}
{%- for script in data.scripts %}
%{_bindir}/{{ script|script_name_for_python_version(pv, minor=False, default_number=False) }}
{%- endfor %}
{%- endif %}
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
{% endcall %}

%changelog
* {{ data.changelog_date_packager }} - {{ data.version }}-1
- Initial package.
