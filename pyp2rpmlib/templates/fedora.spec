%global pypi_name {{ data.name }}

Name:           {% if data.name == data.pkg_name %}{{ data.name }}{% else %}python-%{pypi_name}{% endif %}
Version:        {{ data.version }}
Release:        1%{?dist}
Summary:        {{ data.summary }}

License:        {{ data.license }}
URL:            {{ data.release_url }}
Source0:        {{ data.url }}

{%- if not data.has_extension %}
BuildArch:      noarch
{%- endif %}
BuildRequires:  python-devel

%description
{{ data.description }}


%prep
%setup -q -n %{pypi_name}-%{version}
{%- if data.has_bundled_egg_info %}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
{%- endif %}


%build
{% if data.has_extension %}CFLAGS="$RPM_OPT_FLAGS" {% endif %}%{__python} setup.py build


%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}


%files
%doc
%{python_sitelib}/%{pypi_name}
%{python_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
{%- if data.has_extension %}
%{python_sitearch}/%{pypi_name}
{%- endif %}


%changelog
{{ data.changelog_date_packager }} - {{ data.version }}-1
- Initial package.
