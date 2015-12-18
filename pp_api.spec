Name:           pp_api
Version:        0.1
Release:        0%{?dist}
Summary:        Product Pages API
Group:          Development/Languages
License:        GPL
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python-setuptools
Requires:       python-requests

%description
Product Pages API

%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
# install app
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

%files
%{python_sitelib}/*
%{_bindir}/*

%changelog
* Fri Dec 18 2015 Wei Shi <wshi@redhat.com> - 0.1-0
- Create app
