protocols bgp neighbor bmp route-monitoring adj-in pre-policy
-------------------------------------------------------------

**Minimum user role:** operator

Enable exporting BGP neighbor adjacency-in pre-policy tables. The configuration applies to all BGP neighbor address-families.

**Command syntax: adj-in pre-policy [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor bmp route-monitoring
- protocols bgp neighbor-group bmp route-monitoring
- protocols bgp neighbor-group neighbor bmp route-monitoring

**Note**

- Pre-policy information is exported only when a neighbor is enabled with "soft-reconfiguration inbound", which ensures that the neighbor pre-policy information is kept in BGP.

**Parameter table**

+-------------+-------------------------------+--------------+---------+
| Parameter   | Description                   | Range        | Default |
+=============+===============================+==============+=========+
| admin-state | adjecenty in pre policy table | | enabled    | \-      |
|             |                               | | disabled   |         |
+-------------+-------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bmp route-monitoring
    dnRouter(cfg-neighbor-bmp-rm)# adj-in pre-policy disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bmp route-monitoring
    dnRouter(cfg-group-bmp-rm)# adj-in pre-policy enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bmp route-monitoring
    dnRouter(cfg-group-bmp-rm)# adj-in pre-policy disabled
    dnRouter(cfg-group-bmp-rm)# exit
    dnRouter(cfg-group-bmp)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 1.1.1.1
    dnRouter(cfg-bgp-group-neighbor)# bmp route-monitoring
    dnRouter(cfg-neighbor-bmp-rm)# adj-in pre-policy enabled


**Removing Configuration**

To return the admin-state to the default value:
::

    dnRouter(cfg-neighbor-bmp-rm)# no adj-in pre-policy

::

    dnRouter(cfg-group-bmp-rm)# no adj-in pre-policy

::

    dnRouter(cfg-neighbor-bmp-rm)# no adj-in pre-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
