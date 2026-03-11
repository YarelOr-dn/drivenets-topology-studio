network-services vrf instance protocols bgp neighbor-group neighbor bfd bfd-type
--------------------------------------------------------------------------------

**Minimum user role:** operator

Define the requested BFD session type, Single-hop or Multi-hop. By default session type is according to BGP peering type.

To set requested session type:

**Command syntax: bfd-type [session-type]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group neighbor bfd
- protocols bgp neighbor bfd
- protocols bgp neighbor-group bfd
- protocols bgp neighbor-group neighbor bfd
- network-services vrf instance protocols bgp neighbor bfd
- network-services vrf instance protocols bgp neighbor-group bfd

**Note**

- For multi-hop session type , update-source must be configured for neighbor

- For single-hop session type , bgp peering must be directly over a connected interface

- Reconfig of bfd-type will result in a new BFD session

**Parameter table**

+--------------+----------------------------------------------------------------------------------+----------------+---------+
| Parameter    | Description                                                                      | Range          | Default |
+==============+==================================================================================+================+=========+
| session-type | Define the requested BFD session type, Single-hop or Multi-hop. By default       | | automatic    | \-      |
|              | session type is according to BGP peering type                                    | | single-hop   |         |
|              |                                                                                  | | multi-hop    |         |
+--------------+----------------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bfd
    dnRouter(cfg-bgp-neighbor-bfd)# bfd-type single-hop

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# bfd-type enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 7018
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bfd
    dnRouter(cfg-bgp-group-bfd)# bfd-type multi-hop
    dnRouter(cfg-bgp-group-bfd)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# bfd
    dnRouter(cfg-group-neighbor-bfd)# bfd-type automatic


**Removing Configuration**

To revert the bfd-type to its default value:
::

    dnRouter(cfg-bgp-neighbor-bfd)# no bfd-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
