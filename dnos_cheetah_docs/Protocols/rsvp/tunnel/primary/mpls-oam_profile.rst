protocols rsvp tunnel primary mpls-oam profile
----------------------------------------------

**Minimum user role:** operator

This command associates an MPLS-OAM profile ("services mpls-oam profile") defining a periodic LSP ping test with the specific tunnel. When a profile is associated with the tunnel, and the profile is enabled ("services mpls-oam profile admin-state"), MPLS echo request packets will be sent over the tunnel as part of the periodic probe. 

To associate a profile with a primary tunnel:

**Command syntax: mpls-oam profile [mpls-oam-profile]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel primary
- protocols rsvp tunnel bypass primary
- protocols rsvp auto-bypass primary
- protocols rsvp auto-mesh tunnel-template primary

**Note**
.. -  Available for all tunnel types
..
.. -  Changing mpls-oam profile configuration, attaching a different profile or removing the currently atteched profile will immiditaly stop current running probe an act by the probe .. result.
..
.. -  'no mpls-oam profile' - remove all mpls-oam profile attached to the tunnel

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| mpls-oam-profile | The profile name of the mpls oam service - the profile is atteched for an mpls   | | string         | \-      |
|                  | protocol (e.g RSVP)                                                              | | length 1-255   |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# mpls-oam profile P_1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)# mpls-oam profile P_1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)# mpls-oam profile P_1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-mesh
    dnRouter(cfg-protocols-rsvp-auto-mesh)# tunnel-template TEMP_1
    dnRouter(cfg-rsvp-auto-mesh-temp)# primary
    dnRouter(cfg-auto-mesh-temp-primary)# mpls-oam profile P_1


**Removing Configuration**

To remove the profile association:
::

    dnRouter(cfg-rsvp-tunnel-primary)# no mpls-oam profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
