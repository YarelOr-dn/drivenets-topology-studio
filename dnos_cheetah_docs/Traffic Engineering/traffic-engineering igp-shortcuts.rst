traffic-engineering igp-shortcuts
---------------------------------

**Minimum user role:** operator

IGP shortcuts (IGP-SC) allow the IGP to install routes to indirect destination in the MPLS-NH table in addition to the destination. IGP takes all the destinations in its internal routing table and treats them as if they were directly connected to the local router, thus recreating its topology.

IGP-shortcuts will only enable to resolve BGP and static-route next-hop by a LSP. By default, the BGP and static-route next-hop is first solved by an LSP only if the LSP destination matches the next-hop address. With IGP-shortcuts enabled, BGP and static-route next-hop can be solved by an LSP even if the LSP destination doesn’t match the next-hop address. An IGP path is found to the next-hop destination with the option of using LSPs as a connected route for the IGP topology.

An RSVP tunnel always has preference over an LDP LSP for next-hop resolution.

When an RSVP tunnel is configured for a specific igp-instance, only that instance can use the tunnel as shortcut.

Any change in IGP update, including the removal of the IGP protocol, will affect the computed shortcuts.

The IGP-shortcut SPF calculation runs whenever:

-	IGP SPF calculation runs

-	A tunnel state changes to up or down, or the tunnel is removed

To enable or disable the use of an LSP (either RSVP tunnels or LDP LSP) to resolve non-MPLS traffic:

**Command syntax: igp-shortcuts [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Parameter table**

+----------------+---------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                |                                                                                                                           |             |             |
| Parameter      | Description                                                                                                               | Range       | Default     |
+================+===========================================================================================================================+=============+=============+
|                |                                                                                                                           |             |             |
| admin-state    | The administrative state of the IGP-shortcut   feature. When enabled, IGP-shortcuts will be used by all IGP instances.    | Enabled     | Disabled    |
|                |                                                                                                                           |             |             |
|                |                                                                                                                           | Disabled    |             |
+----------------+---------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# igp-shortcuts enabled

**Removing Configuration**

To revert to the default state:
::

	dnRouter(cfg-protocols-mpls-te)# no igp-shortcuts


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+