protocols ospfv3 area interface bfd
-----------------------------------

**Minimum user role:** operator

To enable BFD protection for ospfv3, use the following command on the interface on which you enabled OSPFv3:


**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area interface

**Note**

- The ospfv3 BFD session type is Single Hop.

- The BFD source address is the ospfv3 interface source address, and the BFD destination address is the ospfv3 peer address.

- When a BFD session is down, the ospfv3 session will be closed and all routes learned from the a neighbor will be withdrawn.

- BFD works in asynchronous mode. BFD established before the ospfv3 adjacency will depend on BFD only once ospfv3 adjacency is full.

- The BFD failure detection time is calculated out of the negotiated received interval and the remote multiplier configurations. The Detection-time = negotiated-received-interval X received multiplier. This is the maximum amount of time that can elapse without receiving a BFD control packet before the session is declared as down.

- A BFD neighbor can signal session state down, and upon receiving a local BFD session, it will immediately switch to DOWN state.

- no bfd command returns the interface bfd paramaters to their default which is taken from the related area BFD configuration.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if-bfd)# bfd
    dnRouter(cfg-ospfv3-area-if-bfd)#


**Removing Configuration**

To disable the ospf area bfd:
::

    dnRouter(cfg-ospfv3-area-if-bfd)# no bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
