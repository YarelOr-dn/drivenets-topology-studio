protocols rsvp tunnel destination-address
-----------------------------------------

**Minimum user role:** operator

A tunnel's destination-address is the tunnel's tail-end router's address.
To configure the tunnel's destination-address for a tunnel or bypass-tunnel:

**Command syntax: destination-address [destination-address]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel

**Note**
- This command is mandatory for tunnel creation.

- This command does not apply to auto-bypass tunnels, whose destination is set according to the protected primary tunnel.

**Parameter table**

+---------------------+-------------------------+---------+---------+
| Parameter           | Description             | Range   | Default |
+=====================+=========================+=========+=========+
| destination-address | rsvp tunnel destination | A.B.C.D | \-      |
+---------------------+-------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# destination-address 1.1.1.1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# destination-address 1.1.1.1


**Removing Configuration**

To remove the tunnel's destination-address, run the command with a new destination address:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# destination-address 5.5.5.5

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 9.0     | Command introduced                      |
+---------+-----------------------------------------+
| 10.0    | Added support for manual bypass tunnels |
+---------+-----------------------------------------+
