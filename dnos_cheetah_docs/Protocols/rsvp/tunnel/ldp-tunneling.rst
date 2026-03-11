protocols rsvp tunnel ldp-tunneling
-----------------------------------

**Minimum user role:** operator

You can enable an rsvp tunnel to be used for LDP tunneling over RSVP. When the tunnel is in Up state, a targeted LDP session will be open to a peer matching the rsvp tunnel destination
To enable/disable the LDP tunneling over RSVP:

**Command syntax: ldp-tunneling [ldp-tunneling]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel
- protocols rsvp auto-mesh tunnel-template

**Note**
- RSVP tunnel ldp-shortcuts-sync is not supported for bypass tunnels (auto and manual).

**Parameter table**

+---------------+-----------------------------------------------------------+--------------+----------+
| Parameter     | Description                                               | Range        | Default  |
+===============+===========================================================+==============+==========+
| ldp-tunneling | Enable rsvp tunnel to be used for LDP tunneling over RSVP | | enabled    | disabled |
|               |                                                           | | disabled   |          |
+---------------+-----------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# ldp-tunneling enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-mesh
    dnRouter(cfg-protocols-rsvp-auto-mesh)# tunnel-template TEMP_1
    dnRouter(cfg-rsvp-auto-mesh-temp)# ldp-tunneling enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no ldp-tunneling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
