
%global pypi_name Jinja2

Name:           %{pypi_name}
Version:        2.8
Release:        %mkrel 1
Summary:        A small but fast and easy to use stand-alone template engine written in pure python
Group:          Development/Python
License:        BSD
URL:            http://jinja.pocoo.org/
Source0:        https://files.pythonhosted.org/packages/source/J/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python2dist(babel) >= 0.8
BuildRequires:  python2dist(markupsafe)
BuildRequires:  python2dist(setuptools)
BuildRequires:  python2dist(sphinx)

%description
Jinja2 is a template engine written in pure Python. It provides a Django_
inspired non-XML syntax but supports inline expressions and an optional
sandboxed_ environment.Nutshell Here a small example of a Jinja template:: {%
extends 'base.html' %} {% block title %}Memberlist{% endblock %} {% block
content %} <ul> {% for user in users %} <li><a href"{{ user.url }}">{{
user.username }}</a></li>...

%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}

Requires:       python2dist(babel) >= 0.8
Requires:       python2dist(markupsafe)
%description -n python2-%{pypi_name}
Jinja2 is a template engine written in pure Python. It provides a Django_
inspired non-XML syntax but supports inline expressions and an optional
sandboxed_ environment.Nutshell Here a small example of a Jinja template:: {%
extends 'base.html' %} {% block title %}Memberlist{% endblock %} {% block
content %} <ul> {% for user in users %} <li><a href"{{ user.url }}">{{
user.username }}</a></li>...

%package -n %{pypi_name}-doc
Summary:        Jinja2 documentation
%description -n %{pypi_name}-doc
Documentation for Jinja2

%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build
# generate html docs
PYTHONPATH=${PWD} sphinx-build-2 docs html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%py2_install

%check
%{__python2} setup.py test

%files -n python2-%{pypi_name}
%license docs/_themes/LICENSE LICENSE
%doc README.rst
%{python2_sitelib}/jinja2
%{python2_sitelib}/%{pypi_name}-%{version}-py%{python2_version}.egg-info

%files -n %{pypi_name}-doc
%doc html
%license docs/_themes/LICENSE LICENSE
%changelog
* Sat Apr 18 2020 Charles K Barcza/Miklos Horvath <info@blackpanther.hu> 2.8-1bP
- Initial pyp2rpm package.
