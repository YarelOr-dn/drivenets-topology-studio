protocols rsvp tunnel bypass
----------------------------

**Minimum user role:** operator

A manual bypass tunnel is a backup LSP used for fast reroute protection. The tunnel is created the moment it is attached to an RSVP interface. The following are the properties of a manually configured bypass tunnel:

- It inherently includes a constraint to avoid the interface it bypasses.
- Its source address is the IPv4 address of the interface it protects (non-configurable). This address must differ from the source-address of the primary LSP it protects.
- Its destination address is configurable (see "rsvp tunnel destination-address" on page 2723
- The default parameter values for a manual bypass tunnel are:

- bandwidth = 0 mbps
- exclude-srlg = avoid
- admin-group = ignore
- class-type = 0
- igp-instance - the IGP instance of the interface configured in IGP (e.g. IS-IS)
- cspf-calculation = enabled, equal cost = least-fill
- primary hop-limit = 255

To manually create a bypass tunnel and enter its configuration mode:

**Command syntax: tunnel [tunnel-bypass] bypass**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- You cannot remove a manual bypass tunnel if it is attached to an RSVP interface.

-  A tunnel name cannot start with "auto\_tunnel\_" or "tunnel\_bypass\_".

.. -  a tunnel name cannot start with tunnel\_bypass\_

.. -  A tunnel is unique by its name, for all bypass and regular tunnels

.. -  a tunnel name cannot include spaces

.. -  no commands remove the manual-bypass RSVP tunnel.

.. -  cannot remove a manual-bypass RSVP tunnel while it's attached to a RSVP interface.

**Parameter table**

+---------------+-------------+------------------+---------+
| Parameter     | Description | Range            | Default |
+===============+=============+==================+=========+
| tunnel-bypass | tunnel name | | string         | \-      |
|               |             | | length 1-255   |         |
+---------------+-------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)#


**Removing Configuration**

To remove a manual bypass tunnel:
::

    dnRouter(cfg-protocols-rsvp)# no tunnel MAN_BACKUP_1

**Command History**

+---------+------------------------------------------------------------------------------------+
| Release | Modification                                                                       |
+=========+====================================================================================+
| 10.0    | Command introduced                                                                 |
+---------+------------------------------------------------------------------------------------+
| 11.0    | Added restrictions on tunnel names to not start with auto_tunnel or tunnel_bypass. |
+---------+------------------------------------------------------------------------------------+
