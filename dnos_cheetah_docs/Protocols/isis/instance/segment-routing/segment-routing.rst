protocols isis instance segment-routing
---------------------------------------

**Minimum user role:** operator

A router in a Segment Routing network can select any path to forward traffic, whether explicit or Interior Gateway Protocol (IGP) shortest path. Each segment in the path to a network destination has an identifier (a segment ID - SID) that is distributed throughout the network via IGP extensions.

To use segment routing with IS-IS, you need to configure these commands:

#.      Optional. Set the segment routing global block (SRGB) and segment routing local block (SRLB) label ranges that will be used by each segment routing-enabled router in the network. You can do this globally for all IGPs (see "routing-options segment-routing mpls global-block" and "routing-options segment-routing mpls local-block") or within the IGP (see "isis instance segment-routing global-block" and "isis instance segment-routing local-block"). If you do not explicitly configure label block ranges, default ranges will be used.

#.      Enable segment routing for an IS-IS instance.

#.      Set the router's node-SID.

#.      Optional. Set the administrative-distance for IS-IS segment-routing. If you do not explicitly configure the administrative-distance, the default value will be used.

To enter IS-IS segment-routing configuration level:

**Command syntax: segment-routing**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- Segment-routing is only available for ipv4-unicast address family.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# segment-routing
    dnRouter(cfg-isis-inst-sr)#


**Removing Configuration**

To revert all IS-IS segment-routing configuration to their default values:
::

    dnRouter(cfg-protocols-isis-inst)# no segment-routing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
