# Created by pyp2rpm-3.2.3
%global pypi_name StructArray

Name:           python-%{pypi_name}
Version:        0.1
Release:        1%{?dist}
Summary:        Fast operations on arrays of structured data

License:        MIT
URL:            http://matthewmarshall.org/projects/structarray/
Source0:        %{pypi_source}

BuildRequires:  python2-devel
BuildRequires:  python2dist(setuptools)

%description
 StructArray StructArray allows you to perform fast arithmetic operations on
arrays of structured (or unstructured) data.This library is useful for
performing the same operation on every item in an I've included an example
showing a simple particle engine. It animates 10,000 particles without much
trouble.*This is the "release early" part of the "release early, release often"
equation. It's...

%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}

%description -n python2-%{pypi_name}
 StructArray StructArray allows you to perform fast arithmetic operations on
arrays of structured (or unstructured) data.This library is useful for
performing the same operation on every item in an I've included an example
showing a simple particle engine. It animates 10,000 particles without much
trouble.*This is the "release early" part of the "release early, release often"
equation. It's...


%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build

%install
%py2_install

%check
%{__python2} setup.py test

%files -n python2-%{pypi_name}
%{python2_sitearch}/%{pypi_name}
%{python2_sitearch}/%{pypi_name}-%{version}-py%{python2_version}.egg-info

%changelog
* Wed Dec 06 2017 Michal Cyprian <mcyprian@redhat.com> - 0.1-1
- Initial package.
