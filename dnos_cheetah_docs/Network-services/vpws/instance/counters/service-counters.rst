network-services vpws instance counters service-counters
--------------------------------------------------------

**Minimum user role:** operator

The Service-counters global setting defines the default setting for VPWS services.
This knob, specifies whether service-counters will be alloocated for this VPWS instance.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance counters

**Parameter table**

+------------------+--------------------------------------------------------------------------+--------------+----------+
| Parameter        | Description                                                              | Range        | Default  |
+==================+==========================================================================+==============+==========+
| service-counters | Define whether service-counters should be allocated for the VPWS service | | enabled    | disabled |
|                  |                                                                          | | disabled   |          |
+------------------+--------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vpws
    dnRouter(cfg-netsrv-evpn)# instance vpws1
    dnRouter(cfg-netsrv-vpws-inst)# counters
    dnRouter(cfg-vpws-inst-counters) service-counters disabled


**Removing Configuration**

To revert the service-counters configuration to its default value of disabled.
::

    dnRouter(cfg-vpws-inst-counters)# no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
