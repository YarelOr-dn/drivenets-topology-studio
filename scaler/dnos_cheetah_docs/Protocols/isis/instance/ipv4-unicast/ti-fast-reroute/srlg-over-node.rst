protocols isis instance address-family ipv4-unicast ti-fast-reroute srlg-over-node
----------------------------------------------------------------------------------

**Minimum user role:** operator

When protection mode is “node-protection" and a slrg-disjoint is required, the system by default will try and find lfa path by the following phases:
1. Find a protection path that provides both srlg-disjoint and node protection.
2. If none are found, find a protection path that provides node protection (assuming srlg-mode is not strict).
3. If none are found, find a protection path that provides both srlg-disjoint and link protection.
4. If none are found, find a protection path that provides link protection (assuming srlg-mode is not strict).

If srlg disjointment is preferred over providing node protection, the user must enable srlg-over-node. This will result in the system trying to find an lfa path by the following phases:
1. Find a protection path that provides both srlg-disjoint and node protection.
2. If none are found, find a protection path that provides both srlg-disjoint and link protection.
3. If none are found, find a protection path that provides node protection (assuming srlg-mode is not strict).
4. If none are found, find a protection path that provides link protection (assuming srlg-mode is not strict).

To enable srlg-over-node:

**Command syntax: srlg-over-node [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast ti-fast-reroute

**Note**

- The configuration has no effect if protection mode is not "node-protection", or if the srlg-mode is strict.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | In case node protection with srlg-disjoint is required, define that              | | enabled    | disabled |
|             | srlg-disjointment is more important to be provided than node protection          | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# srlg-over-node enabled
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# srlg-over-node enabled


**Removing Configuration**

To revert the srlg-over-node to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no srlg-over-node

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
