protocols rsvp tunnel bypass bfd admin-state
--------------------------------------------

**Minimum user role:** operator

Enables a BFD over MPLS session for tunnel LSP protection.

To enable/disable a tunnel, manual bypass tunnel, or auto-bypass tunnel:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass bfd

**Note**
- Configuring the BFD parameter will trigger LSP make-before-break to comply with new BFD state.

.. -  no command returns admin-state to default value

.. -  configuring bfd parameter will trigger LSP make-before-break to comply with new BFD state

**Parameter table**

+-------------+--------------------------------------+------------+----------+
| Parameter   | Description                          | Range      | Default  |
+=============+======================================+============+==========+
| admin-state | Set whether bfd protection is in use | enabled    | disabled |
|             |                                      | disabled   |          |
+-------------+--------------------------------------+------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# bfd
    dnRouter(cfg-rsvp-tunnel-bfd)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# bfd
    dnRouter(cfg-rsvp-bypass-tunnel-bfd)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# bfd
    dnRouter(cfg-rsvp-auto-bypass-bfd)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
