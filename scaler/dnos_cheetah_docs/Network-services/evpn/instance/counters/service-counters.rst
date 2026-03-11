network-services evpn instance counters service-counters
--------------------------------------------------------

**Minimum user role:** operator

The Service-counters global setting defines the default setting for EVPN services.
This knob, specifies whether service-counters will be alloocated for this EVPN instance.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance counters

**Parameter table**

+------------------+---------------------------------------------------------------------------+--------------+---------+
| Parameter        | Description                                                               | Range        | Default |
+==================+===========================================================================+==============+=========+
| service-counters | Define whether service-counters should be allocated for this EVPN service | | enabled    | \-      |
|                  |                                                                           | | disabled   |         |
+------------------+---------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# counters
    dnRouter(cfg-evpn-inst-counters) service-counters disabled


**Removing Configuration**

To revert the service-counters configuration to the evpn global default value
::

    dnRouter(cfg-evpn-inst-counters)# no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
