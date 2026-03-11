protocols rsvp auto-bypass bfd multiplier
-----------------------------------------

**Minimum user role:** operator

The multiplier defines the number of min-rx intervals in which a BFD packet is not received before the session goes down. Using the example below, if min-rx is configured to 100 msec and the multiplier is 4, this means that if BFD packets stop arriving the session will go down after 400 msec.

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bypass bfd
- protocols rsvp tunnel bfd
- protocols rsvp auto-mesh tunnel-template bfd

**Note**
- Configuring the BFD parameter will trigger LSP make-before-break to comply with new BFD state.

**Parameter table**

+------------+--------------------------+-------+---------+
| Parameter  | Description              | Range | Default |
+============+==========================+=======+=========+
| multiplier | set local BFD multiplier | 2-16  | 3       |
+------------+--------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# bfd
    dnRouter(cfg-rsvp-tunnel-bfd)# multiplier 4

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# bfd
    dnRouter(cfg-rsvp-bypass-tunnel-bfd)# multiplier 4

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# bfd
    dnRouter(cfg-rsvp-auto-bypass-bfd)# multiplier 4


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
