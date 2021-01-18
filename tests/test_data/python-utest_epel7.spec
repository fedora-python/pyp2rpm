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

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools

%description


%package -n     python%{python3_pkgversion}-%{pypi_name}
Summary:        Micro test module

Requires:       python%{python3_pkgversion}-pyp2rpm < 3.4
Requires:       python%{python3_pkgversion}-pyp2rpm >= 3.3.1
%description -n python%{python3_pkgversion}-%{pypi_name}



%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%{__python3} setup.py build

%install
%{__python3} setup.py install --skip-build --root %{buildroot}

%files -n python%{python3_pkgversion}-%{pypi_name}
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py%{python3_version}.egg-info

%changelog
*  - 0.1.0-1
- Initial package.
