protocols rsvp tunnel bypass bfd min-rx
---------------------------------------

**Minimum user role:** operator

To set desired minimum receive interval for BFD session:

**Command syntax: min-rx [min-rx]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass bfd

**Note**
- Configuring the BFD parameter will trigger LSP make-before-break to comply with new BFD state.

**Parameter table**

+-----------+------------------------------------------------------+---------+---------+
| Parameter | Description                                          | Range   | Default |
+===========+======================================================+=========+=========+
| min-rx    | Set desired minimum receive interval for BFD session | 50..1700| 300     |
+-----------+------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# bfd
    dnRouter(cfg-rsvp-tunnel-bfd)# min-rx 350

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# bfd
    dnRouter(cfg-rsvp-bypass-tunnel-bfd)# min-rx 350

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# bfd
    dnRouter(cfg-rsvp-auto-bypass-bfd)# min-rx 350


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no min-rx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
