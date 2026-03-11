protocols segment-routing mpls
------------------------------

**Minimum user role:** operator

Segment routing is a mechanism for source-based packet forwarding, where the source router pre-selects a path to the destination and encodes it in the packet header as an ordered list of segments. A segment is an instruction consisting of a flat unsigned 20-bit identifier (the segment ID – SID) and is encoded as an MPLS label. The interior gateway protocol (IGP) distributes two types of segments: prefix SIDs and adjace ncy SIDs. The segment routing configuration level allows you to configure the segment routing global block (SRGB) and local block (SRLB) that will be used by the router. Every node in the domain will receive a node SID from the global block, and every adjacency formed by each router receives a SID from the router's local block.

In the following example, the global-block is from 16000 to 23999, and so all nodes within the domain receive a node SID within this range. Each node is configured with an SRLB range, and so every adjacency formed by that node receives an adjacency SID from within the configured local block.


**Command syntax: mpls**

**Command mode:** config

**Hierarchies**

- protocols segment-routing

**Note**
- The SRGB and SRLB ranges affect the label pools assigned to other MPLS protocols such as RSVP, BGP, and LDP label pools.


**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)#


**Removing Configuration**

To remove the mpls segment-routing configuration:
::

    dnRouter(cfg-protocols-sr)# no mpls

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
