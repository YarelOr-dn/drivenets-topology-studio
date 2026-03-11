traffic-engineering admin-group-map bit-position
------------------------------------------------

**Minimum user role:** operator

An admin-group-map is a bit field where each bit represents a specific admin-group (set by “bit-position”). You can set a traffic-engineering enabled interface with different admin-groups. RSVP uses the admin-group values to decide where tunnels are permitted to flow.

Bits 0-31 used to represent legacy Administrative group mapping per RFC5305 . Bits 32-255 used to represent Extended Administrative group mapping per RFC7308

The bit-position and admin-group name pairing is unique. You cannot set the same admin-group name with a different bit-position and you cannot pair the same bit-position with different admin-group names.

To create an admin-group-map:

**Command syntax: bit-position [bit-position] name [admin-group-name]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Note**

- Changing the admin-group will trigger MPLS TE tunnel calculation (make before brake).

**Parameter table**

+---------------------+--------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                |                      |             |
| Parameter           | Description                                                                    | Range                | Default     |
+=====================+================================================================================+======================+=============+
|                     |                                                                                |                      |             |
| bit-position        | The position of the bit representing a specific   admin-group                  | 0..31                | \-          |
+---------------------+--------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                |                      |             |
| admin-group-name    | Provide a name for the admin-group. The name   represents the bit-position.    | 1..255 characters    | \-          |
+---------------------+--------------------------------------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# admin-group-map
	dnRouter(cfg-mpls-te-admin-group-map)# bit-position 1 name GOLD
	dnRouter(cfg-mpls-te-admin-group-map)# bit-position 2 name SILVER

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# admin-group-map
	dnRouter(cfg-mpls-te-admin-group-map)# bit-position 140 name PLATINUM


**Removing Configuration**

To remove an existing admin-group:
::

	dnRouter(cfg-mpls-te-admin-group-map)# no bit-position 1


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 9.0         | Command introduced    |
+-------------+-----------------------+
| 18.0        | Added Extended        |
|             | admin-group support   |
+-------------+-----------------------+