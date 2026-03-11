protocols rsvp rib-unicast-install
----------------------------------

**Minimum user role:** operator

With the rib-unicast-install command, you can install RSVP tunnel destinations in the RIB IPv4-unicast table as directly reachable through the tunnel.
To enable/disable the ability to install the tunnel destinations in the RIB:

**Command syntax: rib-unicast-install [rib-unicast-install]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- This configuration is applicable to all primary tunnel types (regular and auto-mesh), except bypass tunnels.

.. - RSVP administrative-distance is 100 by default

.. - 'no rib-unicast-install'- return rib-unicast-install to default state

**Parameter table**

+---------------------+-----------------------------------------------------------------------------+--------------+----------+
| Parameter           | Description                                                                 | Range        | Default  |
+=====================+=============================================================================+==============+==========+
| rib-unicast-install | state if tunnel destination will be installed in the rib ipv4-unicast table | | enabled    | disabled |
|                     |                                                                             | | disabled   |          |
+---------------------+-----------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# rib-unicast-install enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-mesh
    dnRouter(cfg-protocols-rsvp-auto-mesh)# tunnel-template TEMP_1
    dnRouter(cfg-rsvp-auto-mesh-temp)# rib-unicast-install enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# rib-unicast-install disabled
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# rib-unicast-install enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# rib-unicast-install enabled
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# rib-unicast-install disabled


**Removing Configuration**

To return the rib-unicast-install to the default:
::

    dnRouter(cfg-protocols-rsvp)# no rib-unicast-install

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
