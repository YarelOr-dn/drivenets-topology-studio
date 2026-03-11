protocols segment-routing mpls igp-shortcuts
--------------------------------------------

**Minimum user role:** operator

IGP shortcuts (IGP-SC) allow the IGP to install routes to indirect destination in the MPLS-NH table in addition to the destination. IGP takes all the destinations in its internal routing table and treats them as if they were directly connected to the local router, thus recreating its topology.
When enabled, an IGP configured with SR extensions will use the SR-TE policy information to calculate a new IGP-MPLS topology, where the SR-TE policies are considered as next-hop for resolution of IGP routes. This makes the SIDs "behind" the SR-TE policy destination reachable using the segment-routing policy.
IGP-Shortcuts results in installing both FTN route and ILM routes using SR-TE policies as next-hops:

•	For FEC-To-NHLFE (FTN) routes, a route is the prefix for which a shortcut was calculated.
•	For Incoming Label Map (ILM) routes, in-label is the matching route SPF prefix-sid, and the next-hop is via SR-TE policy. 

Only policies enabled with a destination-rib that is "mpls-forwarding" or "both" are valid for use as next-hops in shortcuts for ILM routes. If no valid policy next-hop is found, no route will be installed.

To enable or disable the use of a segment-routing policy as shortcuts in calculating segment-routing paths:


**Command syntax: igp-shortcuts [sr-shortcuts]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls

**Note**
- This command may be also be invoked inside mesh-group peer or inside default-peer configuration hierarchy.

- The hold-time timer must be greater than the igp-shortcuts timer. The user is warned in case the igp-shortcuts timer is greater or equal to hold-time.


**Parameter table**

+--------------+-------------------------------------------------------------------+--------------+----------+
| Parameter    | Description                                                       | Range        | Default  |
+==============+===================================================================+==============+==========+
| sr-shortcuts | Configure usage of SR policy as shortcuts in calculating SR paths | | enabled    | disabled |
|              |                                                                   | | disabled   |          |
+--------------+-------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# igp-shortcuts enabled


**Removing Configuration**

To return the igp-shortcuts setting to its default value:
::

    dnRouter(cfg-protocols-igp-mpls)# no igp-shortcuts

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
