protocols isis instance address-family ipv4-multicast fast-reroute level level-2
--------------------------------------------------------------------------------

**Minimum user role:** operator

This command defines the administrative state of fast-reroute per IS-IS instance ipv4-multicast topology.
If enabled, all interfaces currently configured as fast-reroute backup-candidate will be eligible for LFA calculation.
This means that for each interface through which IS-IS prefixes are learned as best, the backup path will be calculated accordingly.
Once enabled, fast-reroute state is set for level-2.
Fast reroute alternate paths for prefix of level-2 is only available through level-1.


**Command syntax: fast-reroute level level-2 [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast

**Note**

- Fast-reroute level-1-2 settings will be default settings for fast-reroute level-1 and fast-reroute level-2

**Parameter table**

+-------------+----------------------------------------+--------------+---------+
| Parameter   | Description                            | Range        | Default |
+=============+========================================+==============+=========+
| admin-state | Enable ISIS LFA (fast-reroute) setting | | enabled    | \-      |
|             |                                        | | disabled   |         |
+-------------+----------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# fast-reroute level level-2 enabled


**Removing Configuration**

To revert fast-reroute level-2 state to default value:
::

    dnRouter(cfg-isis-inst-afi)# no fast-reroute level level-2

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
