# Created by pyp2rpm-3.0.1
%global pypi_name Jinja2

Name:           python-%{pypi_name}
Version:        2.8
Release:        1%{?dist}
Summary:        A small but fast and easy to use stand-alone template engine written in pure python

License:        BSD
URL:            http://jinja.pocoo.org/
Source0:        https://pypi.python.org/packages/f2/2f/0b98b06a345a761bec91a079ccae392d282690c2d8272e708f4d10829e22/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python-setuptools
BuildRequires:  python2-devel
BuildRequires:  python-sphinx
 
Requires:       python-MarkupSafe
Requires:       python-setuptools

%description

Jinja2
~~~~~~

Jinja2 is a template engine written in pure Python.  It
provides a
`Django`_ inspired non-XML syntax but supports inline expressions
and
an optional `sandboxed`_ environment.

Nutshell
--------

Here a small
example of a Jinja template::

    {% extends 'base.html' %}
    {% block title
%}Memberlist{% endblock %}
    {% block content %}
      <ul>
      {% for user
in users %}
 ...


%prep
%setup -q -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

# generate html docs 
sphinx-build docs html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%build
%{__python2} setup.py build


%install
%{__python2} setup.py install --skip-build --root %{buildroot}

%files
%doc html README.rst docs/_themes/LICENSE LICENSE
%{python2_sitelib}/jinja2
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info


%changelog
* Thu May 05 2016 Michal Cyprian <mcyprian@redhat.com> - 2.8-1
- Initial package.
