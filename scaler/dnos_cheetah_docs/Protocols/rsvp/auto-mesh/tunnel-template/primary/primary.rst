protocols rsvp auto-mesh tunnel-template primary
------------------------------------------------

**Minimum user role:** operator

To configure a primary tunnel, manual bypass tunnel, or auto-bypass tunnel:

**Command syntax: primary**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template
- protocols rsvp tunnel
- protocols rsvp tunnel bypass
- protocols rsvp auto-bypass

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# primary
    dnRouter(cfg-rsvp-auto-bypass-primary)#


**Removing Configuration**

To revert all primary LSP's configuration to default:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no primary

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 9.0     | Command introduced                                 |
+---------+----------------------------------------------------+
| 10.0    | Added support for bypass tunnels (manual and auto) |
+---------+----------------------------------------------------+
