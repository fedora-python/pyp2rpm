{{ data.credit_line }}
{% from 'macros.spec' import dependencies, for_python_versions, underscored_or_pypi -%}

{# For all python_versions, prints caller content.
   Content is surrounded by conditionals if python_version != base_python_version #}
{%- macro for_python_versions(python_versions, base_python_version, use_with=True) %}
{%- for pv in python_versions %}
{%- if pv != base_python_version and use_with %}
%if %{with python{{ pv }}}
{% endif %}
{{- caller(pv) }}
{%- if pv != base_python_version and use_with %}
%endif
{% endif %}
{%- endfor %}
{%- endmacro %}

{# Foreach all python_versions, prints caller content.
   Content is surrounded by conditionals if use_with is True #}
{%- macro foreach_python_versions(caller, use_with=True, v='') %}
{%- for pv in [data.base_python_version] + data.python_versions %}
{%- if use_with %}
%if %{with python{{ pv }}}
{%- endif %}
{# set v variable to be '' for python2, '3' for python3 #}
{%- set v = pv|replace(data.base_python_version, '') %}
{{- caller(pv, v) }}
{%- if use_with %}
%endif
{% endif %}
{%- endfor %}
{%- endmacro %}


#
# Conditional build:
%bcond_without	doc	# don't build doc
%bcond_without	tests	# do not perform "make test"
{%- for pv in [data.base_python_version] + data.python_versions %}
%bcond_without	python{{ pv }} # CPython {{ pv }}.x module
{%- endfor %}

%define 	module		{{ data.name }}
%define 	egg_name	{{ data.underscored_name }}
%define		pypi_name	{{ data.name }}
Summary:	{{ data.summary }}
Name:		python-%{pypi_name}
Version:	{{ data.version }}
Release:	0.1
License:	{{ data.license }}
Group:		Libraries/Python
Source0:	{{ data.url|replace(data.name, '%{pypi_name}')|replace(data.version, '%{version}') }}
# Source0-md5:	-
URL:		{{ data.home_page }}
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.714
{# build deps for each Python version #}
{%- for pv in [data.base_python_version] + data.python_versions %}
%if %{with python{{ pv }}}
{{ dependencies(data.build_deps, False, pv, data.base_python_version, False) }}
%endif
{%- endfor %}
{%- if not data.has_extension %}
BuildArch:	noarch
{%- endif %}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
{{ data.description|truncate(400)|wordwrap }}

{% call(pv) for_python_versions(data.python_versions, use_with=False) -%}
%package -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}
Summary:	{{ data.summary }}
Group:		Libraries/Python

%description -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}
{{ data.description|truncate(400)|wordwrap }}
{%- endcall %}

%prep
%setup -q -n %{pypi_name}-%{version}
{%- if data.has_bundled_egg_info %}

# Remove bundled egg-info
%{__rm} -r %{egg_name}.egg-info
{%- endif %}

{% call(pv) for_python_versions([data.base_python_version] + data.python_versions, data.base_python_version, use_with=False) -%}
{%- if data.sphinx_dir %}
# generate html docs {# TODO: generate properly for other versions (pushd/popd into their dirs...) #}
{% if pv != data.base_python_version %}python{{ pv }}-{% endif %}sphinx-build {{ data.sphinx_dir }} html
# remove the sphinx-build leftovers
%{__rm} -r html/.{doctrees,buildinfo}
{%- endif %}
{% endcall %}

%build
{%- call(pv, v) foreach_python_versions(use_with=True) -%}

%py{{ v }}_build %{?with_tests:test}

{%- endcall %}

%install
rm -rf $RPM_BUILD_ROOT
{%- call(pv, v) foreach_python_versions(use_with=True) -%}

%py{{ v }}_install

{%- if pv == data.base_python_version %}
%py_postclean
{%- endif %}

{%- if data.scripts %}
{%- for script in data.scripts %}
mv $RPM_BUILD_ROOT%{_bindir}/{{ script }} $RPM_BUILD_ROOT%{_bindir}/{{ script|script_name_for_python_version(pv) }}
{%- endfor %}
{%- endif %}

{%- endcall %}

%clean
rm -rf $RPM_BUILD_ROOT

{% call(pv, v) foreach_python_versions(use_with=True) -%}
%files{% if pv != data.base_python_version %} -n {{ data.pkg_name|macroed_pkg_name(data.name)|name_for_python_version(pv) }}{% endif %}
%defattr(644,root,root,755)

%doc {% if data.sphinx_dir %}html {% endif %}{{ data.doc_files|join(' ') }}

{%- if data.scripts %}
{%- for script in data.scripts %}
%attr(755,root,root) %{_bindir}/{{ script|script_name_for_python_version(pv) }}
{%- endfor %}
{%- endif %}

{%- if data.py_modules %}
{% for module in data.py_modules -%}
{%- if pv == '2' -%}
%{py{{ v }}_sitescriptdir}/{{ data.name | module_to_path(module) }}.py[co]
{%- endif %}
{%- if pv == '3' -%}
%{py{{ v }}_sitescriptdir}/{{ data.name | module_to_path(module) }}.py
%{py{{ v }}_sitescriptdir}/__pycache__/*
{%- endif %}
{%- endfor %}
{%- endif %}

{%- if data.has_extension %}
%{py{{ v }}_sitedir/%{module}
{%- if data.has_pth %}
%{py{{ v }}_sitedir/%{egg_name}-%{version}-py*-*.pth
{%- endif %}
%{py{{ v }}_sitedir/%{egg_name}-%{version}-py*.egg-info
{%- else %}
{%- if data.has_packages %}
%{py{{ v }}_sitescriptdir}/%{module}
{%- endif %}

{%- if data.has_pth %}
%{py{{ v }}_sitescriptdir}/%{egg_name}-%{version}-py*-*.pth
{%- endif %}
%{py{{ v }}_sitescriptdir}/%{egg_name}-%{version}-py*.egg-info
{%- endif %}

{%- endcall %}
