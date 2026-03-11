network-services vrf instance routing-options maximum-routes address-family maximum
-----------------------------------------------------------------------------------

**Minimum user role:** operator

The maximum number of routes for the address family. The system should not install more than maximum number of prefixes into the FIB unless the warning-only leaf is specified
To set maximum route limit:

**Command syntax: maximum [max-routes]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance routing-options maximum-routes address-family

**Note**

- In case RIB enforce maximum route limit by not installing to FIB an installed RIB route of a given protocol, blackholing may happen

**Parameter table**

+------------+------------------------------------------------+--------------+---------+
| Parameter  | Description                                    | Range        | Default |
+============+================================================+==============+=========+
| max-routes | The maximum number VRF routes RIB will install | 0-4294967295 | \-      |
+------------+------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# routing-options
    dnRouter(cfg-vrf-inst-routing-options)# maximum-routes address-family IPV4
    dnRouter(cfg-inst-routing-options-max-routes)# maximum 5000


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-inst-routing-options-max-routes)# no maximum

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
