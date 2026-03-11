network-services evpn-vpws instance counters service-counters
-------------------------------------------------------------

**Minimum user role:** operator

The Service-counters global setting defines the default setting for EVPN-VPWS services.
This knob, specifies whether service-counters will be alloocated for this EVPN-VPWS instance.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance counters

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
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# counters
    dnRouter(cfg-evpn-vpws-inst-counters) service-counters disabled


**Removing Configuration**

To revert the service-counters configuration to the evpn-vpws global default value
::

    dnRouter(cfg-evpn-vpws-inst-counters)# no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
