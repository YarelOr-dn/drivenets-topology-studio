network-services evpn-vpws-fxc counters service-counters
--------------------------------------------------------

**Minimum user role:** operator

Service-counters disabled is the default setting for EVPN-VPWS-FXC services.
By disabling this knob, service-counters will be disabled for all EVPN-VPWS-FXC instances, that do not have a per-instance configuration.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc counters

**Parameter table**

+------------------+--------------------------------------------------------------------------------+--------------+----------+
| Parameter        | Description                                                                    | Range        | Default  |
+==================+================================================================================+==============+==========+
| service-counters | Define whether service-counters should be allocated for EVPN-VPWS-FXC services | | enabled    | disabled |
|                  |                                                                                | | disabled   |          |
+------------------+--------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# counters
    dnRouter(cfg-netsrv-evpn-vpws-fxc-counters) service-counters enabled


**Removing Configuration**

To revert the service-counters configuration to its default of disabled
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc)# no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
