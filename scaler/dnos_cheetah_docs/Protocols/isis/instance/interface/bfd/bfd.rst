protocols isis instance interface bfd
-------------------------------------

**Minimum user role:** operator

BFD single hop session is used to protected IS-IS link reachability. The BFD session is establish when an IS-IS adjacency is formed. The interface IP address serves as the BFD source address and the IS-IS neighbor address for the given interface serves as the BFD destination address.

To configure BFD protection for IS-IS (BFD must be configured on this interface):


**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Note**

- When the BFD session goes down, IS-IS is notified for the neighbor adjacency state changes to take effect.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# isis-level level-1-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# bfd
    dnRouter(cfg-inst-if-bfd)#


**Removing Configuration**

To revert all BFD configuration to their default values:
::

    dnRouter(cfg-isis-inst-if)# no bfd

**Command History**

+---------+----------------------+
| Release | Modification         |
+=========+======================+
| 6.0     | Command introduced   |
+---------+----------------------+
| 9.0     | Command removed      |
+---------+----------------------+
| 12.0    | Command reintroduced |
+---------+----------------------+
