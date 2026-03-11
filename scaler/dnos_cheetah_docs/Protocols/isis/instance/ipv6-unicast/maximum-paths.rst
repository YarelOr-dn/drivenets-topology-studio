protocols isis instance address-family ipv6-unicast maximum-paths
-----------------------------------------------------------------

**Minimum user role:** operator

To configure IS-IS to install multiple paths with equal cost in the routing table:

**Command syntax: maximum-paths [maximum-paths]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Note**

- The configuration is per address-family and applies regardless of the IS-IS topology enabled.

**Parameter table**

+---------------+-------------------------------------------------------+-------+---------+
| Parameter     | Description                                           | Range | Default |
+===============+=======================================================+=======+=========+
| maximum-paths | The number of routes to install in the routing table. | 1-64  | 8       |
+---------------+-------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# maximum-paths 12
    dnRouter(cfg-isis-inst-afi)# exit
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# maximum-paths 24


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-isis-inst-afi)# no maximum-paths

**Command History**

+---------+------------------------------------------------------------------------+
| Release | Modification                                                           |
+=========+========================================================================+
| 6.0     | Command introduced                                                     |
+---------+------------------------------------------------------------------------+
| 9.0     | Command removed                                                        |
+---------+------------------------------------------------------------------------+
| 10.0    | Command reintroduced under address-family hierarchy (with new default) |
+---------+------------------------------------------------------------------------+
| 15.0    | Updated parameter range from 32 to 64                                  |
+---------+------------------------------------------------------------------------+
