protocols rsvp auto-bandwidth admin-state
-----------------------------------------

**Minimum user role:** operator

To enable auto-bandwidth globally:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bandwidth
- protocols rsvp tunnel auto-bandwidth
- protocols rsvp auto-mesh tunnel-template auto-bandwidth

**Parameter table**

+-------------+-----------------------+--------------+----------+
| Parameter   | Description           | Range        | Default  |
+=============+=======================+==============+==========+
| admin-state | enable auto-bandwidth | | enabled    | disabled |
|             |                       | | disabled   |          |
+-------------+-----------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bandwidth
    dnRouter(cfg-protocols-rsvp-auto-bw)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-auto-bw)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
