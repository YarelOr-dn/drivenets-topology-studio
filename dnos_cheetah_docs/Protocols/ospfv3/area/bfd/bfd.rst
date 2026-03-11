protocols ospfv3 area bfd
-------------------------

**Minimum user role:** operator

Enters ospfv3 area bfd configuration level.


**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area

**Note**

- The Area BFD level is the default per-area interface BFD configuration level.

- OSPFV3 BFD session type is Single-hop.

- BFD source address is the ospfv3 interface source address. BFD destination address is the ospfv3 peer address.

- Upon BFD session down, ospfv3 session will be closed and all routes learnt from neighbor will be withdrawn.

- BFD works in asynchronous mode. Bfd established before the OSPFV3 adjacency, only once OSPFV3 adj. is FULL it will be dependent on BFD.

- BFD failure detection time is computed out of the negotiated received interval and the remote multiplier configurations.

- Detection-time = negotiated-received-interval X received multiplier.

- This is the maximum amount of time that can elapse without receipt of a BFD control packet before the session is declared down.

- BFD neighbor can signal session state down, and upon receipt local bfd session will immediately switch to DOWN state.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# bfd
    dnRouter(cfg-ospfv3-area-bfd)#


**Removing Configuration**

To disable the ospf area bfd:
::

    dnRouter(cfg-protocols-ospfv3-area)# no bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
