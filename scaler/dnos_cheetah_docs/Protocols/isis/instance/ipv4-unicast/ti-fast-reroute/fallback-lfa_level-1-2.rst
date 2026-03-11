protocols isis instance address-family ipv4-unicast ti-fast-reroute fallback-lfa
--------------------------------------------------------------------------------

**Minimum user role:** operator

There may be cases where the ti-fast-reroute path can't be found. For example, not all routers in an IS-IS instance are SR speakers.
To enable fallback on regular igp lfa if no ti-fast-reroute path was found:

**Command syntax: fallback-lfa [fallback-lfa]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast ti-fast-reroute

**Note**

- If the level is not specified, set for all isis supported levels.

- Level-1-2 settings are the default of per level behavior.

**Parameter table**

+--------------+-----------------------------+--------------+----------+
| Parameter    | Description                 | Range        | Default  |
+==============+=============================+==============+==========+
| fallback-lfa | configuration for level-1-2 | | enabled    | disabled |
|              |                             | | disabled   |          |
+--------------+-----------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# fallback-lfa enabled
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# fallback-lfa enabled


**Removing Configuration**

To revert the fallback-lfa to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no fallback-lfa

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
