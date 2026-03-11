protocols rsvp auto-mesh tunnel-template igp-shortcuts
------------------------------------------------------

**Minimum user role:** operator

By default, BGP and static-route next-hops are resolved first by an LSP if the LSP destination matches the next-hop address.
When IGP-shortcuts is enabled, the BGP and static-route next-hop can be solved by the RSVP tunnel even if the tunnel destination doesn’t match the next-hop address. An IGP path is found to the next-hop destination with the option of using LSPs as a connected route for the IGP topology.
An RSVP tunnel will always have preference over LDP for next-hop resolution.

To enable/disable the use of RSVP tunnels to resolve non-MPLS traffic:

**Command syntax: igp-shortcuts [igp-shortcuts]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template
- protocols rsvp tunnel

**Note**
-  RSVP tunnel igp-shortcuts is not supported for bypass tunnels (auto and manual).

-  The RSVP tunnel IGP-shortcuts overrides the "mpls traffic-engineering igp-shortcuts" configuration for the tunnel:

**Parameter table**

+---------------+-----------------------------------------------------------------+--------------+---------+
| Parameter     | Description                                                     | Range        | Default |
+===============+=================================================================+==============+=========+
| igp-shortcuts | support the use of the rsvp tunnel to resolve non mpls traffic. | | enabled    | \-      |
|               |                                                                 | | disabled   |         |
+---------------+-----------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# igp-shortcuts enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)# traffic-engineering
    dnRouter(cfg-protocols-mpls-te)# igp-shortcuts disabled
    dnRouter(cfg-protocols-mpls-te)# exit
    dnRouter(cfg-protocols-mpls)# exit
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# igp-shortcuts enabled


    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)# traffic-engineering
    dnRouter(cfg-protocols-mpls-te)# igp-shortcuts enabled
    dnRouter(cfg-protocols-mpls-te)# exit
    dnRouter(cfg-protocols-mpls)# exit
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# igp-shortcuts disabled


**Removing Configuration**

To return the igp-shortcuts to the default:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no igp-shortcuts

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
