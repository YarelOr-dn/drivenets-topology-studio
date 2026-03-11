protocols bgp neighbor-group bmp activate-server
------------------------------------------------

**Minimum user role:** operator

To enable exporting bgp neighbor information to a bmp server:

**Command syntax: activate-server [server-id]** [, server-id, server-id]

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group bmp
- protocols bgp neighbor bmp
- protocols bgp neighbor-group neighbor bmp

**Note**

- The disabled option is only valid for a neighbor within a neighbor group. When configured, neighbor information is not exported to the bmp server, even if one is configured for the neighbor-group.

**Parameter table**

+-----------+-----------------------------------------------------------+-------+---------+
| Parameter | Description                                               | Range | Default |
+===========+===========================================================+=======+=========+
| server-id | Enable exporting bgp neighbor information to a bmp server | 1-5   | \-      |
+-----------+-----------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# bmp
    dnRouter(cfg-protocols-bgp-neighbor-bmp)# activate-server 1


    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.2.2
    dnRouter(cfg-protocols-bgp-neighbor)# bmp
    dnRouter(cfg-protocols-bgp-neighbor-bmp)# activate-server 1, 2

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bmp
    dnRouter(cfg-protocols-bgp-group-bmp)# activate-server 1
    dnRouter(cfg-protocols-bgp-group-bmp)# activate-server 2

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# bmp
    dnRouter(cfg-protocols-bgp-group-bmp)# activate-server 1
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-bgp-group-neighbor)# bmp
    dnRouter(cfg-group-neighbor-bmp)# activate-server 1

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group GROUP_1
    dnRouter(cfg-protocols-bgp-group)# bmp
    dnRouter(cfg-bgp-group-bmp)# activate-server 1, 2, 3
    dnRouter(cfg-protocols-bgp-group)# neighbor 1.1.1.1
    dnRouter(cfg-bgp-group-neighbor)# bmp activate-server disabled


**Removing Configuration**

To remove the specific bmp server-id:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no bmp activate-server

::

    dnRouter(cfg-protocols-bgp-group)# no bmp activate-server

::

    dnRouter(cfg-bgp-group-neighbor)# no bmp activate-server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
