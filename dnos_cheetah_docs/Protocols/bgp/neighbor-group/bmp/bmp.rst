protocols bgp neighbor-group bmp
--------------------------------

**Minimum user role:** operator

The BGP Monitoring Protocol (BMP) allows you to send the BGP route information from the router to a monitoring application on a separate device. The monitoring application is referred to as the BMP monitoring station or BMP station. To deploy BMP in the network, you need to configure BMP on each router, from which you want to gather information, and at least one BMP station.

BGP BMP collects statistics data from the Adjacency-RIB-In routing tables and send that data periodically to a monitoring station, for further analysis.

Some of the use-cases for BMP include:

- Looking Glasses - IPv4, IPv6, and VPN prefixes.
- Route Analytics - Track convergence times, prefix history as they change over time, monitor and track BGP policy changes, etc...
- Traffic Engineering Analytics - Adapt dynamically to change, and know what is the best shift.
- BGP pre-policy - Pre-policy routing information provides insight into all path attributes from various points in the network, allowing non-intrusive what-if topology views for new policy validations.

**Command syntax: bmp**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group
- protocols bgp neighbor
- protocols bgp neighbor-group neighbor

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bmp
    dnRouter(cfg-bgp-neighbor-bmp)#


    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bmp
    dnRouter(cfg-bgp-group-bmp)#


    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bmp route-monitoring
    dnRouter(cfg-bgp-group-bmp-rm)#
    dnRouter(cfg-bgp-group-bmp-rm)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 1.1.1.1
    dnRouter(cfg-bgp-group-neighbor)# bmp
    dnRouter(cfg-group-neighbor-bmp)#


**Removing Configuration**

To return all bmp settings to the default:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no bmp

::

    dnRouter(cfg-protocols-bgp-group)# no bmp

::

    dnRouter(cfg-bgp-group-neighbor)# no bmp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
