# SAPStartSrv-resourceAgent
pacemaker integration for instance specific sapstartsrv
## Overview

This project is to implement a resource-agent for the instance specific sap start framework. It controls the instance specific
sapstartsrv process which prpvides the API to start, stop and check an SAP instance.

SAPStartSrv does only start, stop and probe for the server process. By intention it does not monitor the service. SAPInstance is doing in-line
recovery of failed sapstartsrv processes instead. 

SAPStartSrv is to be included into a resource group together with the vIP and the SAPInstance. It needs to be started before SAPInstance is starting and
needs to be stopped after SAPInstance is been stopped.

SAPStartSrv could be used since SAP NetWeaver 7.40 or SAP S/4HANA (ABAP Platform >= 1909).

## Resource example

SAPStartSrv could be used where-ever it is not possible to mount/unmount the work directories of the SAPInstances.
The example is based on https://documentation.suse.com/sbp/all/single-html/SAP_NW740_SLE12_SetupGuide/. We replace the file system resource by an SAPStartSrv resource.

```
rsc_sap_HA1_ASCS00 ocf:suse:SAPStartSrv \
         op monitor interval=11 timeout=60 on-fail=ignore \ # <=== !! *)
         params InstanceName=HA1_ASCS00_sapha1as
         # optional: START_PROFILE="/sapmnt/HA1/profile/HA1_ASCS00_sapha1as"
         
group grp_HA1_ASCS00 \
  rsc_ip_HA1_ASCS00 rsc_sap_HA1_ASCS00 rsc_sap_HA1_ASCS00 \
     meta resource-stickiness=3000
```     
