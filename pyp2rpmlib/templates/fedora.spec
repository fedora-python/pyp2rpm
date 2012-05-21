{%- from 'macros.spec' import dependencies %}
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
{% for pv in data.python_versions %}
%if 0%{?with_python{{ pv }}}
%package -n     {{ data.name|macroed_pkg_name|for_python_version(pv) }}
Summary:        {{ data.summary }}

%description -n {{ data.name|macroed_pkg_name|for_python_version(pv) }}
{{ data.description|wordwrap }}
%endif # with_python{{ pv }}
{% endfor %}

%prep
%setup -q -n %{pypi_name}-%{version}
{%- if data.has_bundled_egg_info %}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
{%- endif %}
{% for pv in data.python_versions %}
%if 0%{?with_python{{ pv }}}
rm -rf %{py{{pv}}dir}
cp -a . %{py{{pv}}dir}
find %{py{{pv}}dir} -name '*.py' | xargs sed -i '1s|^#!python|#!%{__python{{pv}}}|'
%endif # with_python{{pv}}
{% endfor %}

%build
{% if data.has_extension %}CFLAGS="$RPM_OPT_FLAGS" {% endif %}%{__python} setup.py build
{% for pv in data.python_versions %}
%if 0%{?with_python{{ pv }}}
pushd %{py{{ pv }}dir}
CFLAGS="$RPM_OPT_FLAGS" %{__python{{ pv }}} setup.py build
popd
%endif # with_python{{ pv }}
{% endfor %}

%install
# Must do the subpackages' install first because the scripts in /usr/bin are
# overwritten with every setup.py install (and we want the python2 version
# to be the default for now).
{%- for pv in data.python_versions %}
%if 0%{?with_python{{ pv }}}
pushd %{py{{ pv }}dir}
%{__python{{ pv }}} setup.py install --skip-build --root $RPM_BUILD_ROOT
popd
%endif # with_python{{ pv }}
{%- endfor %}

%{__python} setup.py install -O1 --skip-build --root %{buildroot}


%files
%doc
%{python_sitelib}/%{pypi_name}
%{python_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
{%- if data.has_extension %}
%{python_sitearch}/%{pypi_name}
{%- endif %}
{% for pv in data.python_versions %}
%if 0%{?with_python{{pv}}}
%files -n {{ data.name|macroed_pkg_name|for_python_version(pv) }}
%doc
%{python{{pv}}_sitelib}/%{pypi_name}
%{python{{pv}}_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
  {%- if data.has_extension %}
%{python{{ pv }}_sitearch}/%{pypi_name}
  {%- endif %}
%endif # with_python{{ pv }}
{% endfor %}

%changelog
* {{ data.changelog_date_packager }} - {{ data.version }}-1
- Initial package.
