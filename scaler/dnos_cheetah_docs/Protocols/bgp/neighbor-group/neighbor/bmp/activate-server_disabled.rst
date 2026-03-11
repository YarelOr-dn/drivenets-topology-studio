protocols bgp neighbor-group neighbor bmp activate-server disabled
------------------------------------------------------------------

**Minimum user role:** operator

Disable exporting bgp neighbor information to a bmp server, while group is set to export bgp information

**Command syntax: activate-server disabled**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group neighbor bmp

**Note**

- Configuration valid for neighbor, neighbor-group and neighbor within a neighbor group

- For neighbor within a group, by default inherit group behavior, if activate server is configure, only support the specific configured servers for that neighbor (i.e do not union with group

- Only a configured bmp server can be set (require auto-complete from configured servers

- Cannot removed server config if there is a neighbor configured to i

- server-id will follow leaf-list behavior, i.e:

- can configured multiple server-ids for a given neighbo

- configuring a server-id will be added to already configured server-id (will not overwrite

- deleting server-id is either per specific id, or removing all servers

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group GROUP_1
    dnRouter(cfg-protocols-bgp-group)# bmp
    dnRouter(cfg-bgp-group-bmp)# activate-server 0, 2, 3
    dnRouter(cfg-protocols-bgp-group)# neighbor 1.1.1.1
    dnRouter(cfg-bgp-group-neighbor)# bmp activate-server disabled


**Removing Configuration**

To remove the specific bmp server:
::

    dnRouter(cfg-bgp-group-neighbor)# no bmp activate-server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
