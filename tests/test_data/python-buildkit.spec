# Created by pyp2rpm-3.1.3
%global pypi_name buildkit

Name:           python-%{pypi_name}
Version:        0.2.2
Release:        1%{?dist}
Summary:        Cloud infrastructure and .deb file management software

License:        GNU AGPLv3
URL:            http://packages.python.org/buildkit
Source0:        https://files.pythonhosted.org/packages/source/b/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  python-setuptools

%description
++++++++.. contents :: Summary Cloud infrastructure and .deb file management
software.Get Started * See the docsAuthor James Gardner <>_Changes20111210 *
Changed aptcacherng to run on port 3142 to avoid a potential conflict with
supervisor20111208 * Separated key generation from install of buildkitaptrepo.
* Made repo and key base directory settings options of the buildkit repo
command so that ...

%package -n     python2-%{pypi_name}
Summary:        Cloud infrastructure and .deb file management software
%{?python_provide:%python_provide python2-%{pypi_name}}

%description -n python2-%{pypi_name}
++++++++.. contents :: Summary Cloud infrastructure and .deb file management
software.Get Started * See the docsAuthor James Gardner <>_Changes20111210 *
Changed aptcacherng to run on port 3142 to avoid a potential conflict with
supervisor20111208 * Separated key generation from install of buildkitaptrepo.
* Made repo and key base directory settings options of the buildkit repo
command so that ...


%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build

%install
%py2_install


%files -n python2-%{pypi_name}
%license LICENSE.txt
%doc example/README.txt README.txt
%{python2_sitelib}/%{pypi_name}
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%changelog
* Thu Sep 22 2016 Michal Cyprian <mcyprian@redhat.com> - 0.2.2-1
- Initial package.
