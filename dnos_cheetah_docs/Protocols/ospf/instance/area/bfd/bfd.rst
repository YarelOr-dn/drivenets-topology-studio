protocols ospf instance area bfd
--------------------------------

**Minimum user role:** operator

Enters ospf area bfd configuration level.


**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Note**

- The Area BFD level is the default per-area interface BFD configuration level

- OSPF BFD session type is Single-hop

- BFD source address is the ospf interface source address. BFD destination address is the ospf peer address

- Upon BFD session down, ospf session will be closed and all routes learnt from neighbor will be withdrawn.

- BFD works in asynchronous mode. Bfd established before the OSPF adjacency, only once OSPF adj. is FULL it will be dependent on BFD.

- BFD failure detection time is computed out of the negotiated received interval and the remote multiplier configurations.

- Detection-time = negotiated-received-interval X received multiplier

- This is the maximum amount of time that can elapse without receipt of a BFD control packet before the session is declared down.

- BFD neighbor can signal session state down, and upon receipt local bfd session will immediately switch to DOWN state

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# bfd
    dnRouter(cfg-ospf-area-bfd)#


**Removing Configuration**

To disable the ospf area bfd:
::

    dnRouter(cfg-protocols-ospf-area)# no bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
