# Created by pyp2rpm-3.2.1
%global pypi_name StructArray

Name:           python-%{pypi_name}
Version:        0.1
Release:        1%{?dist}
Summary:        Fast operations on arrays of structured data

License:        MIT
URL:            http://matthewmarshall.org/projects/structarray/
Source0:        https://files.pythonhosted.org/packages/source/S/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
 
BuildRequires:  python2-devel
BuildRequires:  python-setuptools

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


%files -n python2-%{pypi_name}
%doc 
%{python2_sitearch}/structarray.so
%{python2_sitearch}/%{pypi_name}-%{version}-py?.?.egg-info

%changelog
* Tue Dec 06 2016 Michal Cyprian <mcyprian@redhat.com> - 0.1-1
- Initial package.
