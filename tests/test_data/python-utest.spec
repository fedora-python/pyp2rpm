# Created by pyp2rpm-3.3.3
%global pypi_name utest

Name:           python-%{pypi_name}
Version:        0.1.0
Release:        1%{?dist}
Summary:        Micro test module

License:        GPLv2+
URL:            https://github.com/fedora-python/pyp2rpm
Source0:        %{pypi_name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)

%description


%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

Requires:       (python3dist(pyp2rpm) >= 3.3.1 with python3dist(pyp2rpm) < 3.4)
%description -n python3-%{pypi_name}



%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py3_build

%install
%py3_install

%files -n python3-%{pypi_name}
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py%{python3_version}.egg-info

%changelog
*  - 0.1.0-1
- Initial package.
