protocols rsvp tunnel primary class-type
----------------------------------------

**Minimum user role:** operator

A class type is a set of traffic flows that have the same set of bandwidth constraints. Tunnels of the same class type allocate bandwidth from the same bandwidth pool and tunnels from different class-types will reserve bandwidth from different pools according to the resource allocation model.

The following table shows the class-type to bandwidth pool mapping:

+--------------------+----------------+
|                    |                |
| Bandwidth Pool     | Class-type     |
+====================+================+
| bc0                | 0              |
+--------------------+----------------+
| bc1                | 1              |
+--------------------+----------------+

If the combination of priority (both setup and hold) and class-type is not mapped to a te-class for a tunnel (see "mpls traffic-engineering diffserv-te te-class-map te-class"), the commit will fail.

To assign a tunnel, manual bypass tunnel, or auto-bypass tunnel to a class-type:

**Command syntax: class-type [class-type]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel primary
- protocols rsvp tunnel bypass primary
- protocols rsvp auto-bypass primary
- protocols rsvp auto-mesh tunnel-template primary

**Note**
- Changing the tunnel's class-type for an existing tunnel will cause the tunnel to tear-down before reestablishing it.

- If a bypass tunnel does not satisfy the primary tunnel's constraint, it will not be used for protection.

.. -  if, for any tunnel, the combination priority (both setup and hold) & class-type isn't mapped to a te-class (according to traffic-engineering te-class) commit will fail with .. error message: "No defined TE-Class for tunnel <tunnel-name> with setup-priority <setup-priority> and class-type <class-type>, no bandwidth pool to match".
..
.. -  reconfiguring tunnel class-type for an existing tunnel will cause tunnel to tear-down before reestablishing it.
..
.. -  In case a bypass tunnel doesn't satisfy the primary tunnel constraint, it will not be used for protection
..
.. -  no command returns default class-type

.. -  default tunnel class-type is class-type 0.
..
.. -  class-type to bandwidth pool mapping:

**Parameter table**

+------------+-------------------------------------------------------------+-------+---------+
| Parameter  | Description                                                 | Range | Default |
+============+=============================================================+=======+=========+
| class-type | Assign a tunnel to a class-type when diffserv-te is enabled | 0-1   | 0       |
+------------+-------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# class-type 1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)# class-type 1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# primary
    dnRouter(cfg-rsvp-auto-bypass-primary)# class-type 1


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-rsvp-tunnel-primary)# no class-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
