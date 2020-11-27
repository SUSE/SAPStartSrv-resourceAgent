#
# spec file for package sapstartsrv-resource-agents
#
# Copyright (c) 2017-2020 SUSE LLC.
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
Requires:       python3
BuildRequires:  resource-agents
%if %{with test}
BuildRequires:  python3-mock
BuildRequires:  python3-pytest
%endif

%define raname SAPStartSrv

%description
This is an resource agent for the instance specific SAP start framework.
It controls the instance specific sapstartsrv process which provides the
API to start, stop and check an SAP instance.

Authors:
--------
    Fabian Herschel
    Xabier Arbulu

%prep
%setup -q

%build
gzip man/*

%install
mkdir -p %{buildroot}/usr/lib/ocf/resource.d/suse
mkdir -p %{buildroot}%{_mandir}/man7
mkdir -p %{buildroot}%{_mandir}/man8
mkdir -p %{buildroot}/usr/sbin
mkdir -p %{buildroot}/usr/lib/systemd/system

install -m 0755 ra/%{raname}.in %{buildroot}/usr/lib/ocf/resource.d/suse/%{raname}
install -m 0444 man/*.7.gz %{buildroot}%{_mandir}/man7
install -m 0444 man/*.8.gz %{buildroot}%{_mandir}/man8
install -m 0755 sbin/* %{buildroot}/usr/sbin
install -m 0755 service/* %{buildroot}/usr/lib/systemd/system
sed -i 's+@PYTHON@+%{_bindir}/python3+' %{buildroot}/usr/lib/ocf/resource.d/suse/%{raname}

%if %{with test}
%check
pytest tests
%endif

%files
%defattr(-,root,root)
%if 0%{?sle_version:1} && 0%{?sle_version} < 120300
%doc README.md LICENSE
%doc %{_mandir}/man7/*.7.gz
%doc %{_mandir}/man8/*.8.gz
%else
%doc README.md
%doc %{_mandir}/man7/*.7.gz
%doc %{_mandir}/man8/*.8.gz
%license LICENSE
%endif
%dir /usr/lib/ocf
%dir /usr/lib/ocf/resource.d
%defattr(755,root,root,-)
%dir /usr/lib/ocf/resource.d/suse
%dir /usr/sbin
%dir /usr/lib/systemd/system
/usr/sbin/*
/usr/lib/ocf/resource.d/suse/*
%defattr(644,root,root,-)
/usr/lib/systemd/system/*

%changelog
