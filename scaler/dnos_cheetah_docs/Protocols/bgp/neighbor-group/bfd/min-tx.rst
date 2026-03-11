protocols bgp neighbor-group bfd min-tx
---------------------------------------

**Minimum user role:** operator

Set the desired minimum transmit interval for the BFD session for a single neighbor or neighbor group:

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group bfd
- protocols bgp neighbor bfd
- protocols bgp neighbor-group neighbor bfd
- network-services vrf instance protocols bgp neighbor bfd
- network-services vrf instance protocols bgp neighbor-group bfd
- network-services vrf instance protocols bgp neighbor-group neighbor bfd

**Note**

- This could be invoked inside a neighbor-group or as a single neighbor.

- Neighbors within a neighbor-group derive the neighbor-group configuration or can have a unique setting from the group.

- For neighbors within a neighbor-group, the default value is the group's parameter value.

- Due to hardware limitation, the maximum supported transmit rate is 1700 msec. A negotiated transmit interval higher than 1700 msec will result in an actual transmit rate of 1700 msec.

**Parameter table**

+-----------+-------------------------------------------------------+--------+---------+
| Parameter | Description                                           | Range  | Default |
+===========+=======================================================+========+=========+
| min-tx    | set desired minimum transmit interval for BFD session | 5-1700 | 300     |
+-----------+-------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bfd
    dnRouter(cfg-bgp-neighbor-bfd)# min-tx 400
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# min-tx 400
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# min-tx 400
    dnRouter(cfg-bgp-group-bfd)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# bfd
    dnRouter(cfg-group-neighbor-bfd)# min-tx 300


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-bgp-neighbor-bfd)# no min-tx

::

    dnRouter(cfg-bgp-group-bfd)# no min-tx

::

    dnRouter(cfg-group-neighbor-bfd)# no min-tx

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.4    | Command introduced               |
+---------+----------------------------------+
| 15.1    | Added support for 5msec interval |
+---------+----------------------------------+
