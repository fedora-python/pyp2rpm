# Created by pyp2rpm-3.2.3
%global pypi_name Sphinx
%global srcname sphinx

Name:           python-%{srcname}
Version:        1.5
Release:        1%{?dist}
Summary:        Python documentation generator

License:        BSD
URL:            http://sphinx-doc.org/
Source0:        %{pypi_source}
BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  (python2dist(alabaster) >= 0.7 with python2dist(alabaster) < 0.8)
BuildRequires:  (python2dist(babel) >= 1.3 with (python2dist(babel) < 2 or python2dist(babel) > 2))
BuildRequires:  python2dist(colorama) >= 0.3.5
BuildRequires:  python2dist(docutils) >= 0.11
BuildRequires:  python2dist(html5lib)
BuildRequires:  python2dist(imagesize)
BuildRequires:  python2dist(jinja2) >= 2.3
BuildRequires:  python2dist(mock)
BuildRequires:  python2dist(nose)
BuildRequires:  python2dist(pygments) >= 2
BuildRequires:  python2dist(requests)
BuildRequires:  python2dist(setuptools)
BuildRequires:  python2dist(simplejson)
BuildRequires:  python2dist(six) >= 1.5
BuildRequires:  python2dist(snowballstemmer) >= 1.1
BuildRequires:  python2dist(sqlalchemy) >= 0.9
BuildRequires:  python2dist(whoosh) >= 2

BuildRequires:  python3-devel
BuildRequires:  (python3dist(alabaster) >= 0.7 with python3dist(alabaster) < 0.8)
BuildRequires:  (python3dist(babel) >= 1.3 with (python3dist(babel) < 2 or python3dist(babel) > 2))
BuildRequires:  python3dist(colorama) >= 0.3.5
BuildRequires:  python3dist(docutils) >= 0.11
BuildRequires:  python3dist(html5lib)
BuildRequires:  python3dist(imagesize)
BuildRequires:  python3dist(jinja2) >= 2.3
BuildRequires:  python3dist(mock)
BuildRequires:  python3dist(nose)
BuildRequires:  python3dist(pygments) >= 2
BuildRequires:  python3dist(requests)
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(simplejson)
BuildRequires:  python3dist(six) >= 1.5
BuildRequires:  python3dist(snowballstemmer) >= 1.1
BuildRequires:  python3dist(sqlalchemy) >= 0.9
BuildRequires:  python3dist(whoosh) >= 2
BuildRequires:  python3dist(sphinx)

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

Requires:       (python2dist(alabaster) >= 0.7 with python2dist(alabaster) < 0.8)
Requires:       (python2dist(babel) >= 1.3 with (python2dist(babel) < 2 or python2dist(babel) > 2))
Requires:       python2dist(colorama) >= 0.3.5
Requires:       python2dist(docutils) >= 0.11
Requires:       python2dist(html5lib)
Requires:       python2dist(imagesize)
Requires:       python2dist(jinja2) >= 2.3
Requires:       python2dist(mock)
Requires:       python2dist(nose)
Requires:       python2dist(pygments) >= 2
Requires:       python2dist(requests)
Requires:       python2dist(setuptools)
Requires:       python2dist(simplejson)
Requires:       python2dist(six) >= 1.5
Requires:       python2dist(snowballstemmer) >= 1.1
Requires:       python2dist(sqlalchemy) >= 0.9
Requires:       python2dist(whoosh) >= 2
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

Requires:       (python3dist(alabaster) >= 0.7 with python3dist(alabaster) < 0.8)
Requires:       (python3dist(babel) >= 1.3 with (python3dist(babel) < 2 or python3dist(babel) > 2))
Requires:       python3dist(colorama) >= 0.3.5
Requires:       python3dist(docutils) >= 0.11
Requires:       python3dist(html5lib)
Requires:       python3dist(imagesize)
Requires:       python3dist(jinja2) >= 2.3
Requires:       python3dist(mock)
Requires:       python3dist(nose)
Requires:       python3dist(pygments) >= 2
Requires:       python3dist(requests)
Requires:       python3dist(setuptools)
Requires:       python3dist(simplejson)
Requires:       python3dist(six) >= 1.5
Requires:       python3dist(snowballstemmer) >= 1.1
Requires:       python3dist(sqlalchemy) >= 0.9
Requires:       python3dist(whoosh) >= 2
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
PYTHONPATH=${PWD} sphinx-build-3 doc html
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
%{python2_sitelib}/%{pypi_name}-%{version}-py%{python2_version}.egg-info

%files -n python3-%{srcname}
%license LICENSE
%doc README.rst
%{_bindir}/sphinx-apidoc
%{_bindir}/sphinx-autogen
%{_bindir}/sphinx-build
%{_bindir}/sphinx-quickstart
%{python3_sitelib}/sphinx
%{python3_sitelib}/%{pypi_name}-%{version}-py%{python3_version}.egg-info

%files -n python-%{srcname}-doc
%doc html
%license LICENSE

%changelog
* Wed Dec 06 2017 Michal Cyprian <mcyprian@redhat.com> - 1.5-1
- Initial package.
