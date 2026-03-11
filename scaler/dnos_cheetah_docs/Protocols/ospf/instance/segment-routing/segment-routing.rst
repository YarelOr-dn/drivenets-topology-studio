protocols ospf instance segment-routing
---------------------------------------

**Minimum user role:** operator

A router in a Segment Routing network can select any path to forward traffic, whether explicit or Interior Gateway Protocol (IGP) shortest path. Each segment in the path to a network destination has an identifier (a segment ID - SID) that is distributed throughout the network via IGP extensions.

To use segment routing with OSPF, you need to configure these commands:

#.	Optional, set the segment routing global block (SRGB) and segment routing local block (SRLB) label ranges that will be used by each segment routing-enabled router in the network. You can do this globally for all IGPs (see "routing-options segment-routing mpls global-block" and "routing-options segment-routing mpls local-block") or within the IGP (see "isis instance segment-routing global-block" and "isis instance segment-routing local-block"). If you do not explicitly configure the label block ranges, default ranges will be used.

#.	Enable segment routing for the OSPF.

#.	Set the router's node-SID under the OSPF loopback interface.

#.	Optional, set the administrative-distance for OSPF segment-routing. If you do not explicitly configure the administrative-distance, the default value will be used.

To enter OSPF segment-routing configuration level:

**Command syntax: segment-routing**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# segment-routing
    dnRouter(cfg-protocols-ospf-sr)#


**Removing Configuration**

To revert all segment-routing configuration to default:
::

    dnRouter(cfg-protocols-ospf)# no segment-routing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
