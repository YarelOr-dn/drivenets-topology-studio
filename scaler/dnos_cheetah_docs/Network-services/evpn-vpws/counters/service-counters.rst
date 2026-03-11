network-services evpn-vpws counters service-counters
----------------------------------------------------

**Minimum user role:** operator

Service-counters enabled is the default setting for EVPN-VPWS services.
By disabling this knob, service-counters will be disabled for all EVPN-VPWS instances, that do not have a per-instance configuration.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws counters

**Parameter table**

+------------------+-----------------------------------------------------------------------+--------------+----------+
| Parameter        | Description                                                           | Range        | Default  |
+==================+=======================================================================+==============+==========+
| service-counters | Define whether service-counters should be allocated for EVPN services | | enabled    | disabled |
|                  |                                                                       | | disabled   |          |
+------------------+-----------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# counters
    dnRouter(cfg-netsrv-evpn-vpws-counters) service-counters disabled


**Removing Configuration**

To revert the service-counters configuration to its default of disabled
::

    no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
