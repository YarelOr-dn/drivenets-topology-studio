protocols rsvp auto-mesh tunnel-template ldp-sync
-------------------------------------------------

**Minimum user role:** operator

Enable ldp sync for all tunnels set with ldp-tunneling. When enabled, rsvp tunnel is excluded to be used for ldp tunneling, by either shortcut of forwarding-adjecency, if targeted LDP peer is missing.

**Command syntax: ldp-sync [ldp-sync]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template
- protocols rsvp tunnel

**Parameter table**

+-----------+------------------------------------------+--------------+---------+
| Parameter | Description                              | Range        | Default |
+===========+==========================================+==============+=========+
| ldp-sync  | Set ldp sync for ldp tunneling over rsvp | | enabled    | \-      |
|           |                                          | | disabled   |         |
+-----------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# ldp-sync enabled


**Removing Configuration**

To return the ldp-sync to the default:
::

    dnRouter(cfg-protocols-rsvp)# no ldp-sync

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
