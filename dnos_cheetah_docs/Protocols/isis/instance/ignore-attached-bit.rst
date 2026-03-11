protocols isis instance ignore-attached-bit
-------------------------------------------

**Minimum user role:** operator

When this setting is enabled, if the attached bit is set on an incoming Level-1 IS-IS, the local system ignores it.
In this case the local system does not set a default route to the Level-1-2 router, advertising the PDU with the attached bit set.

**Command syntax: ignore-attached-bit [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Parameter table**

+-------------+---------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                         | Range        | Default  |
+=============+=====================================================================+==============+==========+
| admin-state | Configure IS-IS to ignore attched bit when acting as level-1 router | | enabled    | disabled |
|             |                                                                     | | disabled   |          |
+-------------+---------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# ignore-attached-bit enabled


**Removing Configuration**

To revert the ignore-attached-bit to its default value:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no ignore-attached-bit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
