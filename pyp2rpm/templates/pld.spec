{{ data.credit_line }}
{% from 'macros.spec' import dependencies, for_python_versions, underscored_or_pypi -%}
{%- for pv in data.python_versions %}
%define		with_python{{ pv }} 1
{%- endfor %}
%define		pypi_name	{{ data.name }}
Summary:	{{ data.summary }}
Name:		{{ data.pkg_name|name_for_python_version(data.base_python_version) }}
Version:	{{ data.version }}
Release:	0.1
License:	{{ data.license }}
Group:		Libraries/Python
Source0:	{{ data.url|replace(data.name, '%{pypi_name}')|replace(data.version, '%{version}') }}
# Source0-md5:	-
URL:		{{ data.home_page }}
{{ dependencies(data.build_deps, False, data.base_python_version, data.base_python_version) }}
{%- for pv in data.python_versions %}
{{ dependencies(data.build_deps, False, pv, data.base_python_version) }}
{%- endfor %}
{{ dependencies(data.runtime_deps, True, data.base_python_version, data.base_python_version) }}
{%- if not data.has_extension %}
BuildArch:	noarch
{%- endif %}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
{{ data.description|truncate(400)|wordwrap }}
{% call(pv) for_python_versions(data.python_versions) -%}
%package -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}
Summary:	{{ data.summary }}
{{ dependencies(data.runtime_deps, True, pv, pv) }}

%description -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}
{{ data.description|truncate(400)|wordwrap }}
{%- endcall %}

%prep
%setup -q -n %{pypi_name}-%{version}
{%- if data.has_bundled_egg_info %}

# Remove bundled egg-info
%{__rm} -r %{pypi_name}.egg-info
{%- endif %}
{% call(pv) for_python_versions([data.base_python_version] + data.python_versions, data.base_python_version) -%}
{%- if pv != data.base_python_version -%}
rm -rf %{py{{pv}}dir}
cp -a . %{py{{pv}}dir}
find %{py{{pv}}dir} -name '*.py' | xargs sed -i '1s|^#!python|#!%{__python{{pv}}}|'
{%- endif %}
{%- if data.sphinx_dir %}
# generate html docs {# TODO: generate properly for other versions (pushd/popd into their dirs...) #}
{% if pv != data.base_python_version %}python{{ pv }}-{% endif %}sphinx-build {{ data.sphinx_dir }} html
# remove the sphinx-build leftovers
%{__rm} -r html/.{doctrees,buildinfo}
{%- endif %}
{% endcall %}

%build
{%- call(pv) for_python_versions([data.base_python_version] + data.python_versions, data.base_python_version) -%}
{%- if pv != data.base_python_version -%}
cd %{py{{ pv }}dir}
{%- endif %}
{% if data.has_extension %}
CC="%{__cc}" \
CFLAGS="%{rpmcflags}" \
{% endif %}{{ '%{__python}'|python_bin_for_python_version(pv) }} setup.py build
{% if pv != data.base_python_version -%}
cd -
{%- endif %}
{%- endcall %}

%install
rm -rf $RPM_BUILD_ROOT
{%- if data.python_versions|length > 0 %}
# Must do the subpackages' install first because the scripts in /usr/bin are
# overwritten with every setup.py install (and we want the python2 version
# to be the default for now).
{%- endif -%}
{%- call(pv) for_python_versions(data.python_versions + [data.base_python_version], data.base_python_version) -%}
{%- if pv != data.base_python_version -%}
cd %{py{{ pv }}dir}
{%- endif %}
{{ '%{__python}'|python_bin_for_python_version(pv) }} setup.py install \
	--skip-build \
	--optimize=2 \
	--root=$RPM_BUILD_ROOT

%py_postclean
{%- if pv != data.base_python_version %}
{%- if data.scripts %}
{%- for script in data.scripts %}
mv $RPM_BUILD_ROOT%{_bindir}/{{ script }} $RPM_BUILD_ROOT%{_bindir}/{{ script|script_name_for_python_version(pv) }}
{%- endfor %}
{%- endif %}
cd -
{%- endif %}
{%- endcall %}

%clean
rm -rf $RPM_BUILD_ROOT

{% call(pv) for_python_versions([data.base_python_version] + data.python_versions, data.base_python_version) -%}
%files{% if pv != data.base_python_version %} -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}{% endif %}
%doc {% if data.sphinx_dir %}html {% endif %}{{ data.doc_files|join(' ') }}
{%- if data.scripts %}
{%- for script in data.scripts %}
%{_bindir}/{{ script|script_name_for_python_version(pv) }}
{%- endfor %}
{%- endif %}
{%- if data.py_modules %}
{% for module in data.py_modules -%}
{%- if pv == '3' -%}
{{ '%{python_sitelib}'|sitedir_for_python_version(pv) }}/__pycache__/*
{%- endif %}
{{ '%{python_sitelib}'|sitedir_for_python_version(pv) }}/{{ data.name | module_to_path(module) }}.py{% if pv != '3'%}*{% endif %}
{%- endfor %}
{%- endif %}

{%- if data.has_extension %}
{{ '%{python_sitearch}'|sitedir_for_python_version(pv) }}/{{ data.name | module_to_path(data.underscored_name) }}
{%- if data.has_pth %}
{{ '%{python_sitearch}'|sitedir_for_python_version(pv) }}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py*-*.pth
{%- endif %}
{{ '%{python_sitearch}'|sitedir_for_python_version(pv) }}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py*.egg-info
{%- else %}
{%- if data.has_packages %}
{{ '%{python_sitelib}'|sitedir_for_python_version(pv) }}/{{ data.name | module_to_path(data.underscored_name) }}
{%- endif %}
{%- if data.has_pth %}
{{ '%{python_sitelib}'|sitedir_for_python_version(pv) }}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py*-*.pth
{%- endif %}
{{ '%{python_sitelib}'|sitedir_for_python_version(pv) }}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py*.egg-info
{%- endif %}
{%- endcall %}
