protocols rsvp auto-mesh tunnel-template source-address
-------------------------------------------------------

**Minimum user role:** operator

A tunnel's source-address is the tunnel's head-end router's address. By default, this would be the router's configured MPLS-TE router-id. You can, however use a different address.
To configure a source-address for the tunnel:

**Command syntax: source-address [source-address]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template
- protocols rsvp tunnel

**Note**
- This command does not apply to bypass tunnels (auto or manual). For auto-bypass and manual bypass tunnels, the RSVP egress interface source address is according to the egress interface.

**Parameter table**

+----------------+------------------------------------------------------+---------+---------+
| Parameter      | Description                                          | Range   | Default |
+================+======================================================+=========+=========+
| source-address | rsvp ip source address to be use in tunnel signaling | A.B.C.D | \-      |
+----------------+------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# source-address 2.2.2.2


**Removing Configuration**

To revert to the default source-address:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no source-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
