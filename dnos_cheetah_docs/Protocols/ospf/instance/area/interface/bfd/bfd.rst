protocols ospf instance area interface bfd
------------------------------------------

**Minimum user role:** operator

Enters the OSPF area BFD configuration level.


**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**

- The Area BFD level is the default per-area interface BFD configuration level.

- The OSPF BFD session type is Single-hop.

- The BFD source address is the OSPF interface source address. The BFD destination address is the OSPF peer address.

- Upon BFD session down, the OSPF session closes and all the routes learnt from the neighbor are withdrawn.

- BFD works in asynchronous mode. When BFD is established before the OSPF adjacency, only once the OSPF adj is full will it be dependent on BFD.

- BFD failure detection time is computed out of the negotiated received interval and the remote multiplier configurations.

- Detection-time = negotiated-received-interval X received multiplier

- This is the maximum amount of time that can elapse without receipt of a BFD control packet before the session is declared down.

- BFD neighbor can signal session state down, and upon receipt the local BFD session will immediately switch to DOWN state.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if-bfd)# bfd
    dnRouter(cfg-ospf-area-if-bfd)#


**Removing Configuration**

To disable the ospf area bfd:
::

    dnRouter(cfg-ospf-area-if-bfd)# no bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
