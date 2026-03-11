protocols isis instance address-family ipv4-multicast maximum-paths
-------------------------------------------------------------------

**Minimum user role:** operator

To configure IS-IS to install multiple paths with equal cost in the routing table:

**Command syntax: maximum-paths [maximum-paths]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast

**Parameter table**

+---------------+--------------------+-------+---------+
| Parameter     | Description        | Range | Default |
+===============+====================+=======+=========+
| maximum-paths | ISIS multiple path | 1-64  | 8       |
+---------------+--------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# maximum-paths 24


**Removing Configuration**

To revert maximum-paths settings to the default value:
::

    dnRouter(cfg-isis-inst-afi)# no maximum-paths

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
