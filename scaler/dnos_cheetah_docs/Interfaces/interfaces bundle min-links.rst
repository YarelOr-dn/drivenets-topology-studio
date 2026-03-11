interfaces min-links
--------------------

**Minimum user role:** operator

You can set a minimum number of member interfaces that must be active for the bundle interface to be available (operational status "up"). For example, if you have a bundle interface with 5 links of 100GbE, and you set min-links to 3, then if one or two links fail, the bundle will still be operational. However, if three links fail, the entire bundle will be down.

If min-bandwidth is configured, both configurations apply. That is, if min-links is set to 2 and min-bandwidth is set to 100Gbps, then the operational status of the bundle interface in the above example will be "down" if three 100Gbps link go down, even though the minimum bandwidth condition is met if four links fail.

The min-link configuration is independent of LACP configuration. If LACP is not enabled, the min-link configuration must be identical on both ends of the bundle link. If LACP is enabled, the LACP state-machine takes precedence over the LAG selection mechanism.

To configure the minimum number of active links in the bundle interface:

**Command syntax: min-links [min-links]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to bundle interfaces.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| min-links | Set the minimum number of interface members that must be active for the          | 1-64  | 1       |
|           | aggregate interface to be available. The operational state of the bundle         |       |         |
|           | interface will remain down until the minimum number of members is reached.       |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# min-links 5


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1)# no min-links

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 6.0     | Command introduced                              |
+---------+-------------------------------------------------+
| 10.0    | Command moved hierarchy from LACP               |
+---------+-------------------------------------------------+
| 13.1    | Increased maximum number of links from 32 to 64 |
+---------+-------------------------------------------------+
