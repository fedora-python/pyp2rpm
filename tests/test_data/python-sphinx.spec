# Created by pyp2rpm-3.2.3
%global pypi_name Sphinx
%global srcname sphinx

Name:           python-%{srcname}
Version:        1.5
Release:        1%{?dist}
Summary:        Python documentation generator

License:        BSD
URL:            http://sphinx-doc.org/
Source0:        https://files.pythonhosted.org/packages/source/S/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildConflicts: python2-babel = 2.0
BuildRequires:  python2-Jinja2 >= 2.3
BuildRequires:  python2-Pygments >= 2.0
BuildRequires:  python2-alabaster < 0.8
BuildRequires:  python2-alabaster >= 0.7
BuildRequires:  python2-babel >= 1.3
BuildRequires:  python2-colorama >= 0.3.5
BuildRequires:  python2-docutils >= 0.11
BuildRequires:  python2-html5lib
BuildRequires:  python2-imagesize
BuildRequires:  python2-mock
BuildRequires:  python2-nose
BuildRequires:  python2-requests
BuildRequires:  python2-setuptools
BuildRequires:  python2-simplejson
BuildRequires:  python2-six >= 1.5
BuildRequires:  python2-snowballstemmer >= 1.1
BuildRequires:  python2-sqlalchemy >= 0.9
BuildRequires:  python2-whoosh >= 2.0
 
BuildRequires:  python3-devel
BuildConflicts: python3-babel = 2.0
BuildRequires:  python3-Jinja2 >= 2.3
BuildRequires:  python3-Pygments >= 2.0
BuildRequires:  python3-alabaster < 0.8
BuildRequires:  python3-alabaster >= 0.7
BuildRequires:  python3-babel >= 1.3
BuildRequires:  python3-colorama >= 0.3.5
BuildRequires:  python3-docutils >= 0.11
BuildRequires:  python3-html5lib
BuildRequires:  python3-imagesize
BuildRequires:  python3-mock
BuildRequires:  python3-nose
BuildRequires:  python3-requests
BuildRequires:  python3-setuptools
BuildRequires:  python3-simplejson
BuildRequires:  python3-six >= 1.5
BuildRequires:  python3-snowballstemmer >= 1.1
BuildRequires:  python3-sqlalchemy >= 0.9
BuildRequires:  python3-whoosh >= 2.0
BuildRequires:  python3-sphinx

%description
Sphinx is a tool that makes it easy to create intelligent and beautiful
documentation for Python projects (or other documents consisting of multiple
reStructuredText sources), written by Georg Brandl. It was originally created
for the new Python documentation, and has excellent facilities for Python
project documentation, but C/C++ is supported as well, and more languages are
Sphinx uses...

%package -n     python2-%{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{srcname}}
 
Conflicts:      python2-babel = 2.0
Requires:       python2-Jinja2 >= 2.3
Requires:       python2-Pygments >= 2.0
Requires:       python2-alabaster < 0.8
Requires:       python2-alabaster >= 0.7
Requires:       python2-babel >= 1.3
Requires:       python2-colorama >= 0.3.5
Requires:       python2-docutils >= 0.11
Requires:       python2-html5lib
Requires:       python2-imagesize
Requires:       python2-mock
Requires:       python2-nose
Requires:       python2-requests
Requires:       python2-setuptools
Requires:       python2-simplejson
Requires:       python2-six >= 1.5
Requires:       python2-snowballstemmer >= 1.1
Requires:       python2-sqlalchemy >= 0.9
Requires:       python2-whoosh >= 2.0
%description -n python2-%{srcname}
Sphinx is a tool that makes it easy to create intelligent and beautiful
documentation for Python projects (or other documents consisting of multiple
reStructuredText sources), written by Georg Brandl. It was originally created
for the new Python documentation, and has excellent facilities for Python
project documentation, but C/C++ is supported as well, and more languages are
Sphinx uses...

%package -n     python3-%{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{srcname}}
 
Conflicts:      python3-babel = 2.0
Requires:       python3-Jinja2 >= 2.3
Requires:       python3-Pygments >= 2.0
Requires:       python3-alabaster < 0.8
Requires:       python3-alabaster >= 0.7
Requires:       python3-babel >= 1.3
Requires:       python3-colorama >= 0.3.5
Requires:       python3-docutils >= 0.11
Requires:       python3-html5lib
Requires:       python3-imagesize
Requires:       python3-mock
Requires:       python3-nose
Requires:       python3-requests
Requires:       python3-setuptools
Requires:       python3-simplejson
Requires:       python3-six >= 1.5
Requires:       python3-snowballstemmer >= 1.1
Requires:       python3-sqlalchemy >= 0.9
Requires:       python3-whoosh >= 2.0
%description -n python3-%{srcname}
Sphinx is a tool that makes it easy to create intelligent and beautiful
documentation for Python projects (or other documents consisting of multiple
reStructuredText sources), written by Georg Brandl. It was originally created
for the new Python documentation, and has excellent facilities for Python
project documentation, but C/C++ is supported as well, and more languages are
Sphinx uses...

%package -n python-%{srcname}-doc
Summary:        Sphinx documentation
%description -n python-%{srcname}-doc
Documentation for Sphinx

%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build
%py3_build
# generate html docs 
sphinx-build-3 doc html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
# Must do the default python version install last because
# the scripts in /usr/bin are overwritten with every setup.py install.
%py2_install
rm -rf %{buildroot}%{_bindir}/*
%py3_install

%check
%{__python2} setup.py test
%{__python3} setup.py test

%files -n python2-%{srcname}
%license LICENSE
%doc README.rst
%{python2_sitelib}/sphinx
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n python3-%{srcname}
%license LICENSE
%doc README.rst
%{_bindir}/sphinx-apidoc
%{_bindir}/sphinx-autogen
%{_bindir}/sphinx-build
%{_bindir}/sphinx-quickstart
%{python3_sitelib}/sphinx
%{python3_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n python-%{srcname}-doc
%doc html
%license LICENSE

%changelog
* Tue Dec 05 2017 Michal Cyprian <mcyprian@redhat.com> - 1.5-1
- Initial package.
