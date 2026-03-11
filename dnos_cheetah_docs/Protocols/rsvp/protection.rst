protocols rsvp protection
-------------------------

**Minimum user role:** operator

Fast reroute protection enables to divert a tunnel passing through a failed interface by encapsulating it in a different tunnel carrying the traffic to a merge point behind the network failure.
There are two types of traffic protection for RSVP-signaled LSPs:

- Link protection - where a bypass tunnel encapsulates the traffic through an LSP skipping the potential damaged link and forwards it towards the protected tunnel's next-hop.

- Node protection - where a bypass tunnel encapsulates the traffic through an LSP skipping the potential damaged node and forwards it towards the protected tunnel's next next-hop.

The bypass-tunnel can have any length LSP (limited by the configured “hop-limit”).

When protection is needed and a bypass tunnel that can provide it (i.e. it has the required destination and matches the required protection type) is available, the bypass tunnel will be used regardless of any conflict with the Primary tunnel's attributes, such as admin-group.
When there are multiple possible bypass-tunnels available for protection, the bypass tunnel that will be used is the “least used” bypass-tunnel, i.e the tunnel that protects the least number of primary tunnels. 

The bypass tunnel protection type supported is facility-backup. A single bypass-tunnel provides protection to multiple primary tunnels. If several (2 or more) primary tunnels are protected by a single protection Bypass (of the same type) and a new protection bypass (of the same type) is created – the bypasses are reselected for protection of the primary tunnels to ensure equal usage of bypass tunnels among the primary tunnels.
You can configure up to 5 manual bypass-tunnels per interface. There is no limit to the number of auto bypass-tunnels established through an interface.
When checking the scale of tunnels in the system, bypass-tunnels (auto and manual) are regarded as any other tunnel and are counted in the system's total tunnel scale limit.

When enabled, all the nodes are informed that the LSP is protected against link and/or node failure. Bypass tunnels that match the protection request are set as protection tunnels. If there are no eligible bypass tunnels and auto-bypass is enabled, an auto-bypass tunnel will be created.

To globally enable/disable fast-reroute tunnel protection:

**Command syntax: protection [protection]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+------------+----------------------------------------------------+---------------------+----------+
| Parameter  | Description                                        | Range               | Default  |
+============+====================================================+=====================+==========+
| protection | global configuration for tunnel protection setting | | disabled          | disabled |
|            |                                                    | | link-protection   |          |
|            |                                                    | | node-protection   |          |
+------------+----------------------------------------------------+---------------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# protection link-protection

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# protection node-protection

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# protection disabled


**Removing Configuration**

To revert protection to the default state:
::

    dnRouter(cfg-protocols-rsvp)# no protection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
