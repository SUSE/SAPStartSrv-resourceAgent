#
# spec file for package SAPStartSrv
#
# Copyright (c) 2013-2014 SUSE Linux Products GmbH, Nuernberg, Germany.
# Copyright (c) 2014-2016 SUSE Linux GmbH, Nuernberg, Germany.
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
Summary:        Resource agent to control SAP instances using sapstartsrv
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

%description
This project is to implement a resource agent for the instance specific SAP start framework. It controls the instance specific sapstartsrv process which provides the API to start, stop and check an SAP instance.

SAPStartSrv does only start, stop and probe for the server process. By intention it does not monitor the service. SAPInstance is doing in-line recovery of failed sapstartsrv processes instead.

SAPStartSrv is to be included into a resource group together with the vIP and the SAPInstance. It needs to be started before SAPInstance is starting and needs to be stopped after SAPInstance has been stopped.

SAPStartSrv can be used since SAP NetWeaver 7.40 or SAP S/4HANA (ABAP Platform >= 1909).

Authors:
--------
    Fabian Herschel
    Xabier Arbulu

%prep
mkdir -p %{name}-%{version}
cd %{name}-%{version}
tar xf %{S:0}
## %setup -q

%build
gzip man/*

%install
mkdir -p %{buildroot}/usr/lib/ocf/resource.d/suse
mkdir -p %{buildroot}%{_mandir}/man7
cp ra/%{name}.in %{buildroot}/usr/lib/ocf/resource.d/suse/%{name}
cp man/*.7 %{buildroot}/usr/share/man/man7/
sed -i 's+@PYTHON@+%{_bindir}/python3+' %{buildroot}/usr/lib/ocf/resource.d/suse/%{name}

install -m 0755 ra/* %{buildroot}/usr/lib/ocf/resource.d/suse/
install -m 0444 man/*.7.gz %{buildroot}%{_mandir}/man7

%if %{with test}
%check
pytest tests
%endif

%files
%defattr(-,root,root)
%if 0%{?sle_version:1} && 0%{?sle_version} < 120300
%doc README.md LICENSE
%doc %{_mandir}/man7/*.7.gz
%else
%doc README.md
%doc %{_mandir}/man7/*.7.gz
%license LICENSE
%endif
%dir /usr/lib/ocf
%dir /usr/lib/ocf/resource.d
%dir %{_mandir}/man7
%defattr(755,root,root,-)
%dir /usr/lib/ocf/resource.d/suse
/usr/lib/ocf/resource.d/suse/*

%changelog
