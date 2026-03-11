protocols isis instance address-family ipv4-multicast fast-reroute
------------------------------------------------------------------

**Minimum user role:** operator

Defines the administrative state of fast-reroute per IS-IS instance ipv4-multicast topology.
If enabled, all interfaces currently configured as fast-reroute backup-candidates will be eligible for LFA calculation.
This means that for each interface through which IS-IS prefixes are learned as best, the backup path will be calculated accordingly.
Once enabled, fast-reroute state is set for both level-1 and level-2 (depending on the IS-IS level).
Fast reroute alternate paths for the prefix of level-1/level-2 are only available through level-1/level-2 nodes respectively.


**Command syntax: fast-reroute [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast

**Note**

- Fast-reroute level-1-2 settings are the default settings for fast-reroute level-1 and fast-reroute level-2

**Parameter table**

+-------------+----------------------------------------+--------------+----------+
| Parameter   | Description                            | Range        | Default  |
+=============+========================================+==============+==========+
| admin-state | Enable ISIS LFA (fast-reroute) setting | | enabled    | disabled |
|             |                                        | | disabled   |          |
+-------------+----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# fast-reroute enabled


**Removing Configuration**

To revert fast-reroute state to default value:
::

    dnRouter(cfg-isis-inst-afi)# no fast-reroute

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
