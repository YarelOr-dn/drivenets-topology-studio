protocols bgp neighbor bmp route-monitoring
-------------------------------------------

**Minimum user role:** operator

To enter the BMP server route-monitoring configuration level:

**Command syntax: route-monitoring**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor bmp
- protocols bgp neighbor-group bmp
- protocols bgp neighbor-group neighbor bmp

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bmp
    dnRouter(cfg-bgp-neighbor-bmp)# route-monitoring
    dnRouter(cfg-neighbor-bmp-rm)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bmp
    dnRouter(cfg-bgp-group-bmp)# route-monitoring
    dnRouter(cfg-group-bmp-rm)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bmp
    dnRouter(cfg-bgp-group-bmp)# route-monitoring
    dnRouter(cfg-group-bmp-rm)#
    dnRouter(cfg-bgp-group-bmp-rm)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 1.1.1.1
    dnRouter(cfg-bgp-group-neighbor)# bmp route-monitoring
    dnRouter(cfg-neighbor-bmp-rm)#


**Removing Configuration**

To return the admin-state to the default value:
::

    dnRouter(cfg-bgp-neighbor-bmp)# no route-monitoring

::

    dnRouter(cfg-bgp-group-bmp)# no route-monitoring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
