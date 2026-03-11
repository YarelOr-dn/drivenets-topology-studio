network-services vrf instance protocols bgp neighbor-group advertisement-interval
---------------------------------------------------------------------------------

**Minimum user role:** operator

To set the interval between BGP routing updates:

**Command syntax: advertisement-interval [advertisement-interval]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group
- protocols bgp neighbor
- protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter              | Description                                                                      | Range | Default |
+========================+==================================================================================+=======+=========+
| advertisement-interval | Set the interval between BGP routing updates. The default advertisement-interval | 0-600 | \-      |
|                        | between ibgp and ebgp sessions default for ibgp = 0 default for ebgp = 30        |       |         |
+------------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# remote-as 5000
    dnRouter(cfg-protocols-bgp-neighbor)# advertisement-interval 20
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001::66
    dnRouter(cfg-protocols-bgp-neighbor)# remote-as 5000
    dnRouter(cfg-protocols-bgp-neighbor)# advertisement-interval 90
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# remote-as 7180
    dnRouter(cfg-protocols-bgp-group)# advertisement-interval 2


**Removing Configuration**

To revert to the default interval:
::

    dnRouter(cfg-protocols-bgp-group)# no advertisement-interval

::

    dnRouter(cfg-protocols-bgp-neighbor)# no advertisement-interval

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 6.0     | Command introduced                               |
+---------+--------------------------------------------------+
| 9.0     | Updated default interval for iBGP neighbors to 0 |
+---------+--------------------------------------------------+
