network-services vrf instance routing-options
---------------------------------------------

**Minimum user role:** operator

Enter routing-options configuration level for non default VRF:

**Command syntax: routing-options**

**Command mode:** config

**Hierarchies**

- network-services vrf instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# routing-options
    dnRouter(cfg-vrf-inst-routing-options)#


**Removing Configuration**

To revert all routing options configuration to default state:
::

    dnRouter(cfg-netsrv-vrf-inst)# no routing-options

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
