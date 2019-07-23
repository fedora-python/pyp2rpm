# Created by pyp2rpm-3.2.3
%global pypi_name Jinja2

Name:           python-%{pypi_name}
Version:        2.8
Release:        1%{?dist}
Summary:        A small but fast and easy to use stand-alone template engine written in pure python

License:        BSD
URL:            http://jinja.pocoo.org/
Source0:        https://files.pythonhosted.org/packages/source/J/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python2-babel >= 0.8
BuildRequires:  python2-markupsafe
BuildRequires:  python2-setuptools
BuildRequires:  python2-sphinx

Requires:       python2-babel >= 0.8
Requires:       python2-markupsafe

%description
Jinja2 is a template engine written in pure Python. It provides a Django_
inspired non-XML syntax but supports inline expressions and an optional
sandboxed_ environment.Nutshell Here a small example of a Jinja template:: {%
extends 'base.html' %} {% block title %}Memberlist{% endblock %} {% block
content %} <ul> {% for user in users %} <li><a href"{{ user.url }}">{{
user.username }}</a></li>...

%package -n python-%{pypi_name}-doc
Summary:        Jinja2 documentation
%description -n python-%{pypi_name}-doc
Documentation for Jinja2

%prep
%setup -q -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

# generate html docs
PYTHONPATH=${PWD} sphinx-build docs html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%build
%{__python2} setup.py build


%install
%{__python2} setup.py install --skip-build --root %{buildroot}
%check
%{__python2} setup.py test


%files
%doc README.rst
%{python2_sitelib}/jinja2
%{python2_sitelib}/%{pypi_name}-%{version}-py%{python2_version}.egg-info

%files -n python-%{pypi_name}-doc
%doc html
%license docs/_themes/LICENSE LICENSE

%changelog
* Wed Dec 06 2017 Michal Cyprian <mcyprian@redhat.com> - 2.8-1
- Initial package.
