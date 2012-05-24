{{ data.credit_line }}
{% from 'macros.spec' import dependencies, for_python_versions -%}
%global pypi_name {{ data.name }}
{%- for pv in data.python_versions %}
%global with_python{{ pv }} 1
{%- endfor %}

Name:           {{ data.pkg_name|macroed_pkg_name }}
Version:        {{ data.version }}
Release:        1%{?dist}
Summary:        {{ data.summary }}

License:        {{ data.license }}
URL:            {{ data.release_url }}
Source0:        {{ data.url }}

{%- if not data.has_extension %}
BuildArch:      noarch
{%- endif %}
{{ dependencies(data.build_deps, False, '') }}
{%- for pv in data.python_versions %}
{{ dependencies(data.build_deps, False, pv) }}
{%- endfor %}
{{ dependencies(data.runtime_deps, True, '') }}
{%- for pv in data.python_versions %}
{{ dependencies(data.runtime_deps, True, pv) }}
{%- endfor %}

%description
{{ data.description|wordwrap }}
{% call(pv) for_python_versions(data.python_versions) -%}
%package -n     {{ data.name|macroed_pkg_name|for_python_version(pv) }}
Summary:        {{ data.summary }}

%description -n {{ data.name|macroed_pkg_name|for_python_version(pv) }}
{{ data.description|wordwrap }}
{%- endcall %}

%prep
%setup -q -n %{pypi_name}-%{version}
{%- if data.has_bundled_egg_info %}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
{%- endif %}
{% call(pv) for_python_versions([''] + data.python_versions) -%}
{%- if pv -%}
rm -rf %{py{{pv}}dir}
cp -a . %{py{{pv}}dir}
find %{py{{pv}}dir} -name '*.py' | xargs sed -i '1s|^#!python|#!%{__python{{pv}}}|'
{%- endif %}
{%- if data.sphinx_dir %}
# generate html docs {# TODO: generate properly for other versions (pushd/popd into their dirs...) #}
{% if pv %}python{{ pv }}-{% endif %}sphinx-build {{ data.sphinx_dir }} html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}
{%- endif %}
{% endcall %}

%build
{%- call(pv) for_python_versions([''] + data.python_versions) -%}
{%- if pv -%}
pushd %{py{{ pv }}dir}
{%- endif %}
{% if data.has_extension %}CFLAGS="$RPM_OPT_FLAGS" {% endif %}%{__python{{ pv }}} setup.py build
{% if pv -%}
popd
{%- endif %}
{%- endcall %}

%install
{%- if data.python_versions|length > 0 %}
# Must do the subpackages' install first because the scripts in /usr/bin are
# overwritten with every setup.py install (and we want the python2 version
# to be the default for now).
{%- endif -%}
{%- call(pv) for_python_versions(data.python_versions + ['']) -%}
{%- if pv -%}
pushd %{py{{ pv }}dir}
{%- endif %}
%{__python{{ pv }}} setup.py install --skip-build --root %{buildroot}
{%- if pv %}
popd
{%- endif %}
{%- endcall %}


%files
%doc {% if data.sphinx_dir %}html {% endif %}{{ data.doc_files|join(' ') }}
{%- if data.has_packages %}
%{python_sitelib}/%{pypi_name}
{%- endif %}
{%- for module in data.py_modules %}
%{python_sitelib}/{% if data.name == module %}%{pypi_name}{% else %}{{ module }}{% endif %}.py*
{%- endfor %}
%{python_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
{%- if data.has_extension %}
%{python_sitearch}/%{pypi_name}
{%- endif %}
{% call(pv) for_python_versions(data.python_versions) -%}
%files -n {{ data.name|macroed_pkg_name|for_python_version(pv) }}
%doc {% if data.sphinx_dir %}html {% endif %}{{ data.doc_files|join(' ') }}
  {%- if data.has_packages %}
%{python{{pv}}_sitelib}/%{pypi_name}
  {%- endif %}
  {%- for module in data.py_modules %}
%{python{{ pv }}_sitelib}/{% if data.name == module %}%{pypi_name}{% else %}{{ module }}{% endif %}.py*
  {%- endfor %}
%{python{{pv}}_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
  {%- if data.has_extension %}
%{python{{ pv }}_sitearch}/%{pypi_name}
  {%- endif %}
{%- endcall %}

%changelog
* {{ data.changelog_date_packager }} - {{ data.version }}-1
- Initial package.
