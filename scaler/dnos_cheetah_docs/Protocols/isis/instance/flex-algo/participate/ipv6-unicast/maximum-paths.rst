protocols isis instance flex-algo participate address-family ipv6-unicast maximum-paths
---------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure IS-IS to install multiple paths with equal cost per flex-algo route in the routing table:

**Command syntax: maximum-paths [maximum-paths]**

**Command mode:** config

**Hierarchies**

- protocols isis instance flex-algo participate address-family ipv6-unicast

**Note**

- Default maximum-paths behavior is per isis instance address-family config

**Parameter table**

+---------------+-------------------------------------------------------+-------+---------+
| Parameter     | Description                                           | Range | Default |
+===============+=======================================================+=======+=========+
| maximum-paths | The number of routes to install in the routing table. | 1-64  | \-      |
+---------------+-------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# flex-algo
    dnRouter(cfg-isis-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)# address-family ipv4-unicast
    dnRouter(cfg-flex-algo-participate-afi)# maximum-paths 12
    dnRouter(cfg-flex-algo-participate-afi)# exit
    dnRouter(cfg-flex-algo-participate)# address-family ipv6-unicast
    dnRouter(cfg-flex-algo-participate-afi)# maximum-paths 12


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-flex-algo-participate-afi)# no maximum-paths

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
