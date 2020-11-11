#
# spec file for package sapstartsrv-resource-agents
#
# Copyright (c) 2020 SUSE LLC.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.
#
# Please submit bugfixes or comments via http://bugs.opensuse.org/

%if 0%{?suse_version} < 1500
%bcond_with test
%else
%bcond_without test
%endif

Name:           sapstartsrv-resource-agents
License:        GPL-2.0
Group:          Productivity/Clustering/HA
AutoReqProv:    on
Summary:        Resource agent for SAP instance specific sapstartsrv service
Version:        0.1.0
Release:        0
Url:            https://github.com/SUSE/SAPStartSrv-resourceAgent

BuildArch:      noarch

Source0:        %{name}-%{version}.tar.gz

BuildRoot:      %{_tmppath}/%{name}-%{version}-build

Requires:       pacemaker > 1.1.1
Requires:       resource-agents
Requires:       python2
BuildRequires:  resource-agents
Distribution:	SUSE Linux Enterprise 12
%if %{with test}
Requires:       python3
BuildRequires:  python3-mock
BuildRequires:  python3-pytest
Distribution:	SUSE Linux Enterprise 15
%endif

%description
This is an resource agent for the instance specific SAP start framework.
It controls the instance specific sapstartsrv process which provides the
API to start, stop and check an SAP instance.

Authors:
--------
    Fabian Herschel
    Xabier Arbulu


%prep
mkdir -p %{name}-%{version}
cd %{name}-%{version}
tar xf %{S:0}

%build
cd %{name}-%{version}
gzip -f man/*.[0-9]
sed -i 's+@PYTHON@+%{_bindir}/python3+' ra/SAPStartSrv.in ra/SAPStartSrv

%install
cd %{name}-%{version} || exit
mkdir -p %{buildroot}/usr/lib/ocf/resource.d/suse
mkdir -p %{buildroot}/%{_mandir}/man7
mkdir -p %{buildroot}/%{_docdir}/%{name}
cp ra/SAPStartSrv.in %{buildroot}/usr/lib/ocf/resource.d/suse/SAPStartSrv
cp man/*.7.gz %{buildroot}/%{_mandir}/man7/
cp README.md LICENSE %{buildroot}/%{_docdir}/%{name}/

%if %{with test}
%check
pytest tests
%endif

%files
%defattr(-,root,root)
%if 0%{?sle_version:1} && 0%{?sle_version} < 120300
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/LICENSE
%doc %{_mandir}/man7/*.7.gz
%else
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/LICENSE
%doc %{_mandir}/man7/*.7.gz
%endif
%dir /usr/lib/ocf
%dir /usr/lib/ocf/resource.d
%dir %{_mandir}/man7
%defattr(755,root,root,-)
%dir /usr/lib/ocf/resource.d/suse
/usr/lib/ocf/resource.d/suse/*

%clean
rm -rf %{buildroot}

%changelog
