protocols isis instance administrative-distance
-----------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.

The administrative distance must be different for all IS-IS instances. The default value is configured for the first IS-IS instance only. For all other instances, you must configure it manually.

To configure the administrative distance for IS-IS:


**Command syntax: administrative-distance [admin-distance]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- When reconfiguring the administrative-distance, clear the IS-IS routes using the "run clear isis routes" command.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                      | Range | Default |
+================+==================================================================================+=======+=========+
| admin-distance | Sets the administrative distance for IS-IS. A value of 255 will cause the router | 1-255 | 115     |
|                | to remove the route from the forwarding table.                                   |       |         |
+----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# administrative-distance 90


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-isis-inst)# no administrative-distance

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 6.0     | Command introduced                    |
+---------+---------------------------------------+
| 9.0     | Removed filtering for external routes |
+---------+---------------------------------------+
| 10.0    | Added rules for multiple instances    |
+---------+---------------------------------------+
