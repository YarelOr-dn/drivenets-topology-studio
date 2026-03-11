protocols bgp neighbor-group neighbor bmp activate-server
---------------------------------------------------------

**Minimum user role:** operator

Enable exporting bgp neighbor information to a bmp server 

 server-id - set to which bmp server table infromation will be exported 

 Can set up to 5 different bmps servers for a given neighbor

 Configuration applies for all bgp neighbor address-families

**Command syntax: activate-server [server-id]** [, server-id, server-id]

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group neighbor bmp
- protocols bgp neighbor bmp
- protocols bgp neighbor-group bmp

**Note**

- Configuration valid for neighbor, neighbor-group and neighbor within a neighbor group

- For neighbor within a group, by default inherit group behavior, if activate server is configure, only support the specific configured servers for that neighbor (i.e do not union with group

- Only a configured bmp server can be set (require auto-complete from configured servers

- Cannot removed server config if there is a neighbor configured to i

- server-id will follow leaf-list behavior, i.e:

- can configured multiple server-ids for a given neighbo

- configuring a server-id will be added to already configured server-id (will not overwrite

- deleting server-id is either per specific id, or removing all servers

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
    dnRouter(cfg-protocols-bgp-neighbor-bmp)# activate-server 0


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
    dnRouter(cfg-protocols-bgp-group-bmp)# activate-server 4
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

To remove the specific bmp server:
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
| 16.1    | Command introduced |
+---------+--------------------+
