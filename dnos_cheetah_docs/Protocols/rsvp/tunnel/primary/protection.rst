protocols rsvp tunnel primary protection
----------------------------------------

**Minimum user role:** operator

Fast reroute protection enables to divert a tunnel passing through a failed interface by encapsulating it in a different tunnel carrying the traffic to a merge point behind the network failure.

There are two types of traffic protection for RSVP-signaled LSPs:

- Link protection - where a bypass tunnel encapsulates the traffic through an LSP skipping the potential damaged link and forwards it towards the protected tunnel's next-hop:
- - When Link protection is desired, and no bypass LSP available to provide the required link protection, no protection will be given.

- Node protection - where a bypass tunnel encapsulates the traffic through an LSP skipping the potential damaged node and forwards it towards the protected tunnel's next next-hop:
- - When Node protection is desired, and no bypass LSP available to provide the required node protection, a link protection will be used if available. 

The bypass-tunnel can have any length LSP (limited by the configured “hop-limit”).
When protection is needed and a bypass tunnel that can provide it (i.e. it has the required destination and matches the required protection type) is available, the bypass tunnel will be used regardless of any conflict with the Primary tunnel's attributes, such as admin-group.
When there are multiple possible bypass-tunnels available for protection, the bypass tunnel that will be used is the “least used” bypass-tunnel, i.e the tunnel that protects the least number of primary tunnels. 

The bypass tunnel protection type supported is facility-backup. A single bypass-tunnel provides protection to multiple primary tunnels. If several (2 or more) primary tunnels are protected by a single protection Bypass (of the same type) and a new protection bypass (of the same type) is created – the bypasses are reselected for protection of the primary tunnels to ensure equal usage of bypass tunnels among the primary tunnels.

You can configure up to 5 manual bypass-tunnels per interface. There is no limit to the number of auto bypass-tunnels established through an interface.
When checking the scale of tunnels in the system, bypass-tunnels (auto and manual) are regarded as any other tunnel and are counted in the system's total tunnel scale limit.
Protection by a bypass tunnel that serves node-protection is preferred over a bypass tunnel that serves link-protection (even if link protection is requested). If a primary tunnel is protected by a link-protection bypass tunnel and a new bypass tunnel is created that serves node-protection, the primary tunnel will switch to be protected by the new bypass tunnel.

If there are both manual and automatic bypass tunnels, they are all eligible for load-balancing of primary tunnels.

When enabled, all the nodes are informed that the LSP is protected against link and/or node failure. Bypass tunnels that match the protection request are set as protection tunnels. If there are no eligible bypass tunnels and auto-bypass is enabled (see "rsvp auto-bypass"), an auto-bypass tunnel will be created.

To enable/disable fast-reroute protection for a tunnel:

**Command syntax: protection [protection]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel primary
- protocols rsvp auto-mesh tunnel-template primary

**Parameter table**

+------------+----------------------------------------------------+---------------------+---------+
| Parameter  | Description                                        | Range               | Default |
+============+====================================================+=====================+=========+
| protection | global configuration for tunnel protection setting | | disabled          | \-      |
|            |                                                    | | link-protection   |         |
|            |                                                    | | node-protection   |         |
+------------+----------------------------------------------------+---------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# protection link

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL2
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# protection node

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL3
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# protection disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-rsvp-tunnel-primary)# no protection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.1    | Command introduced |
+---------+--------------------+
