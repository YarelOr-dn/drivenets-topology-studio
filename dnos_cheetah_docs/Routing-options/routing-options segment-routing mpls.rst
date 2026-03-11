routing-options segment-routing mpls
------------------------------------

**Minimum user role:** operator

Segment routing is a mechanism for source-based packet forwarding, where the source router pre-selects a path to the destination and encodes it in the packet header as an ordered list of segments. A segment is an instruction consisting of a flat unsigned 20-bit identifier (the segment ID – SID) and is encoded as an MPLS label. The interior gateway protocol (IGP) distributes two types of segments: prefix SIDs and adjace ncy SIDs. The segment routing configuration level allows you to configure the segment routing global block (SRGB) and local block (SRLB) that will be used by the router. Every node in the domain will receive a node SID from the global block, and every adjacency formed by each router receives a SID from the router's local block.

To enter the global segment routing configuration level:

**Command syntax: segment-routing mpls**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- The SRGB and SRLB ranges affect the label pools assigned to other MPLS protocols such as RSVP, BGP, and LDP label pools.

- Notice the change in prompt.

.. -  no command returns all segment-routing mpls configurations to their default state

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# segment-routing mpls
	dnRouter(cfg-routing-option-sr)#


**Removing Configuration**

To revert all segment-routing configurations to the default values:
::

	dnRouter(cfg-routing-option)# no segment-routing mpls

.. **Help line:** enters global segment routing configuration level

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+


