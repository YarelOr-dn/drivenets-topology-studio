protocols isis instance level
-----------------------------

**Minimum user role:** operator

IS-IS routers (i.e. Intermediate Systems (IS)), are designated as Level-1 (area routers), Level-2 (domain routers) or Level 1-2 (both area and domain routers). ISs that operate at Level 1 exchange routing information with other Level-1 ISs in the same area. ISs that operate at Level 2 exchange routing information with other Level-2 devices only. The set of Level-2 devices and the links that interconnect them form the Level-2 subdomain, which must not be partitioned in order for routing to work properly.

To configure the router's behavior:


**Command syntax: level [level]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- RSVP-TE and BGP-LS are supported on Level-2 only.

**Parameter table**

+-----------+----------------------------------------+---------------+-----------+
| Parameter | Description                            | Range         | Default   |
+===========+========================================+===============+===========+
| level     | The level at which the router operates | | level-1     | level-1-2 |
|           |                                        | | level-2     |           |
|           |                                        | | level-1-2   |           |
+-----------+----------------------------------------+---------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# level level-2


**Removing Configuration**

To revert to the default router level:
::

    dnRouter(cfg-protocols-isis-inst)# no level

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 6.0     | Command introduced                                         |
+---------+------------------------------------------------------------+
| 9.0     | Removed level-1 and level-1-2 routing                      |
+---------+------------------------------------------------------------+
| 14.0    | Added support for level-1-2 (changed default to level-1-2) |
+---------+------------------------------------------------------------+
| 17.0    | Added support for level-1                                  |
+---------+------------------------------------------------------------+
