protocols rsvp auto-mesh tunnel-template primary hop-limit
----------------------------------------------------------

**Minimum user role:** operator

You can set the maximum number of nodes that the LSP can traverse, including head-end and tail-end nodes. Setting a hop-limit value will add a CSPF constraint that the tunnel path cannot exceed the set number of hops.

To configure the limitation on the number of hops that LSPs can traverse:

**Command syntax: hop-limit [hop-limit]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template primary
- protocols rsvp tunnel primary
- protocols rsvp tunnel bypass primary
- protocols rsvp auto-bypass primary

**Parameter table**

+-----------+-----------------------------------------+-------+---------+
| Parameter | Description                             | Range | Default |
+===========+=========================================+=======+=========+
| hop-limit | the time-to-live value for the mpls lsp | 2-255 | 255     |
+-----------+-----------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# hop-limit 100

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)# hop-limit 100

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# primary
    dnRouter(cfg-rsvp-auto-bypass-primary)# hop-limit 100


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-rsvp-tunnel-primary)# no hop-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
