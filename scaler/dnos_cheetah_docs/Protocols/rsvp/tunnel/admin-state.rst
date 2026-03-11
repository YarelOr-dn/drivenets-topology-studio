protocols rsvp tunnel admin-state
---------------------------------

**Minimum user role:** operator

To enable/disable a tunnel, manual bypass tunnel, or auto-bypass tunnel:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel
- protocols rsvp tunnel bypass
- protocols rsvp auto-mesh tunnel-template

**Parameter table**

+-------------+------------------+--------------+---------+
| Parameter   | Description      | Range        | Default |
+=============+==================+==============+=========+
| admin-state | Set tunnel state | | enabled    | enabled |
|             |                  | | disabled   |         |
+-------------+------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# admin-state disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# admin-state disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
