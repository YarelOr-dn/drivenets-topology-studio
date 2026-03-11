network-services evpn-vpws-fxc instance counters service-counters
-----------------------------------------------------------------

**Minimum user role:** operator

The Service-counters global setting defines the default setting for EVPN-VPWS-FXC services.
This knob, specifies whether service-counters will be allocated for this EVPN-VPWS-FXC instance.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance counters

**Parameter table**

+------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter        | Description                                                                      | Range        | Default |
+==================+==================================================================================+==============+=========+
| service-counters | Define whether service-counters should be allocated for this EVPN-VPWS-FXC       | | enabled    | \-      |
|                  | service                                                                          | | disabled   |         |
+------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# counters
    dnRouter(cfg-evpn-vpws-inst-counters) service-counters enabled


**Removing Configuration**

To revert the service-counters configuration to the evpn-vpws-fxc global default value
::

    dnRouter(cfg-evpn-vpws-inst-counters)# no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
