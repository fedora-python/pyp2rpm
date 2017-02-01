# Created by pyp2rpm-3.2.1
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
BuildRequires:  python-setuptools
BuildRequires:  python-sphinx
 
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

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
 
Requires:       python-six >= 1.5
Requires:       python-Jinja2 >= 2.3
Requires:       python-Pygments >= 2.0
Requires:       python-docutils >= 0.11
Requires:       python-snowballstemmer >= 1.1
Conflicts:      python-babel = 2.0
Requires:       python-babel >= 1.3
Requires:       python-alabaster < 0.8
Requires:       python-alabaster >= 0.7
Requires:       python-imagesize
Requires:       python-requests
Requires:       python-setuptools
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
 
Requires:       python3-six >= 1.5
Requires:       python3-Jinja2 >= 2.3
Requires:       python3-Pygments >= 2.0
Requires:       python3-docutils >= 0.11
Requires:       python3-snowballstemmer >= 1.1
Conflicts:      python3-babel = 2.0
Requires:       python3-babel >= 1.3
Requires:       python3-alabaster < 0.8
Requires:       python3-alabaster >= 0.7
Requires:       python3-imagesize
Requires:       python3-requests
Requires:       python3-setuptools
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
sphinx-build doc html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
# Must do the subpackages' install first because the scripts in /usr/bin are
# overwritten with every setup.py install.
%py3_install
cp %{buildroot}/%{_bindir}/sphinx-quickstart %{buildroot}/%{_bindir}/sphinx-quickstart-%{python3_version}
ln -s %{_bindir}/sphinx-quickstart-%{python3_version} %{buildroot}/%{_bindir}/sphinx-quickstart-3
cp %{buildroot}/%{_bindir}/sphinx-apidoc %{buildroot}/%{_bindir}/sphinx-apidoc-%{python3_version}
ln -s %{_bindir}/sphinx-apidoc-%{python3_version} %{buildroot}/%{_bindir}/sphinx-apidoc-3
cp %{buildroot}/%{_bindir}/sphinx-build %{buildroot}/%{_bindir}/sphinx-build-%{python3_version}
ln -s %{_bindir}/sphinx-build-%{python3_version} %{buildroot}/%{_bindir}/sphinx-build-3
cp %{buildroot}/%{_bindir}/sphinx-autogen %{buildroot}/%{_bindir}/sphinx-autogen-%{python3_version}
ln -s %{_bindir}/sphinx-autogen-%{python3_version} %{buildroot}/%{_bindir}/sphinx-autogen-3

%py2_install
cp %{buildroot}/%{_bindir}/sphinx-quickstart %{buildroot}/%{_bindir}/sphinx-quickstart-%{python2_version}
ln -s %{_bindir}/sphinx-quickstart-%{python2_version} %{buildroot}/%{_bindir}/sphinx-quickstart-2
cp %{buildroot}/%{_bindir}/sphinx-apidoc %{buildroot}/%{_bindir}/sphinx-apidoc-%{python2_version}
ln -s %{_bindir}/sphinx-apidoc-%{python2_version} %{buildroot}/%{_bindir}/sphinx-apidoc-2
cp %{buildroot}/%{_bindir}/sphinx-build %{buildroot}/%{_bindir}/sphinx-build-%{python2_version}
ln -s %{_bindir}/sphinx-build-%{python2_version} %{buildroot}/%{_bindir}/sphinx-build-2
cp %{buildroot}/%{_bindir}/sphinx-autogen %{buildroot}/%{_bindir}/sphinx-autogen-%{python2_version}
ln -s %{_bindir}/sphinx-autogen-%{python2_version} %{buildroot}/%{_bindir}/sphinx-autogen-2


%files -n python2-%{srcname}
%license LICENSE
%doc README.rst
%{_bindir}/sphinx-quickstart
%{_bindir}/sphinx-quickstart-2
%{_bindir}/sphinx-quickstart-%{python2_version}
%{_bindir}/sphinx-apidoc
%{_bindir}/sphinx-apidoc-2
%{_bindir}/sphinx-apidoc-%{python2_version}
%{_bindir}/sphinx-build
%{_bindir}/sphinx-build-2
%{_bindir}/sphinx-build-%{python2_version}
%{_bindir}/sphinx-autogen
%{_bindir}/sphinx-autogen-2
%{_bindir}/sphinx-autogen-%{python2_version}
%{python2_sitelib}/sphinx
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n python3-%{srcname}
%license LICENSE
%doc README.rst
%{_bindir}/sphinx-quickstart-3
%{_bindir}/sphinx-quickstart-%{python3_version}
%{_bindir}/sphinx-apidoc-3
%{_bindir}/sphinx-apidoc-%{python3_version}
%{_bindir}/sphinx-build-3
%{_bindir}/sphinx-build-%{python3_version}
%{_bindir}/sphinx-autogen-3
%{_bindir}/sphinx-autogen-%{python3_version}
%{python3_sitelib}/sphinx
%{python3_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n python-%{srcname}-doc
%doc html 

%changelog
* Fri Nov 25 2016 Iryna Shcherbina <ishcherb@redhat.com> - 1.4.9-1
- Initial package.
