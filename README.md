# SAPStartSrv-resourceAgent
pacemaker integration for instance specific sapstartsrv
## Overview

This project is to implement a resource-agent for the instance specific SAP start framework. It controls the instance specific
sapstartsrv process which provides the API to start, stop and check an SAP instance.

SAPStartSrv does only start, stop and probe for the server process. By intention it does not monitor the service. SAPInstance is doing in-line
recovery of failed sapstartsrv processes instead.

SAPStartSrv is to be included into a resource group together with the vIP and the SAPInstance. It needs to be started before SAPInstance is starting and
needs to be stopped after SAPInstance has been stopped.

SAPStartSrv could be used since SAP NetWeaver 7.40 or SAP S/4HANA (ABAP Platform >= 1909).

## Resource example

SAPStartSrv could be used where-ever it is not possible to mount/unmount the work directories of the SAPInstances.
The example is based on https://documentation.suse.com/sbp/all/single-html/SAP_NW740_SLE12_SetupGuide/. We replace the file system resource by an SAPStartSrv resource.

```
primitive rsc_sapstartsrv_HA1_ASCS00 ocf:suse:SAPStartSrv \
         params InstanceName=HA1_ASCS00_sapha1as         

group grp_HA1_ASCS00 \
  rsc_ip_HA1_ASCS00 rsc_sapstartsrv_HA1_ASCS00 rsc_sap_HA1_ASCS00 \
     meta resource-stickiness=3000
```     

**Note:** The resource **rsc_sapstartsrv_HA1_ASCS00** does by intention not define a monitoring operation. This is, because the failing sapstartsrv must never force an SAP instance restart which would happen, as the two resources reside in one resource group.

**Note:** To use the python version of the resource agent, the shebang of the script file must be changed (this is done during the packaging process). Replace `#!@PYTHON@ -tt` by `#!/usr/bin/python3 -tt` with the correct python version.

## Unit tests

The python version of the resource agent comes with a unit test battery. In order to run them:

```
cd SAPStartSrv-resourceAgent
virtualenv myvirtenv
source myvirtenv/bin/activate
myvirtenv/bin/pip install pytest-cov mock
myvirtenv/bin/py.test -vv --cov=SAPStartSrv --cov-report term tests
```
