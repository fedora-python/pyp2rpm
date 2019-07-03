# Created by pyp2rpm-3.3.2
%global pypi_name paperwork-backend

Name:           python-%{pypi_name}
Version:        1.2.4
Release:        1%{?dist}
Summary:        Paperwork's backend

License:        GPLv3+
URL:            https://github.com/openpaperwork/paperwork-backend
Source0:        https://files.pythonhosted.org/packages/source/p/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)

%description
Paperwork is a GUI to make papers searchable.This is the backend part of
Paperwork. It manages: - The work directory / Access to the documents -
Indexing - Searching - Suggestions- ExportThere is no GUI here. The GUI is .

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

Requires:       python3dist(natsort)
Requires:       python3dist(pillow)
Requires:       python3dist(pycountry)
Requires:       python3dist(pyenchant)
Requires:       python3dist(pyocr)
Requires:       python3dist(python-levenshtein)
Requires:       python3dist(setuptools)
Requires:       python3dist(simplebayes)
Requires:       python3dist(termcolor)
Requires:       python3dist(whoosh)
%description -n python3-%{pypi_name}
Paperwork is a GUI to make papers searchable.This is the backend part of
Paperwork. It manages: - The work directory / Access to the documents -
Indexing - Searching - Suggestions- ExportThere is no GUI here. The GUI is .


%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py3_build

%install
%py3_install

%files -n python3-%{pypi_name}
%license LICENSE
%doc README.markdown
%{_bindir}/paperwork-shell
%{python3_sitelib}/paperwork_backend
%{python3_sitelib}/paperwork_backend-%{version}-py%{python3_version}.egg-info

%changelog
* Thu Mar 21 2019 Miro Hrončok <mhroncok@redhat.com> - 1.2.4-1
- Initial package.
