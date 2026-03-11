interfaces destination
----------------------

**Minimum user role:** operator

To configure the tunnel's destination endpoint:

**Command syntax: destination [ipv4-address]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the gre-tunnel interface.

- You cannot create multiple GRE tunnels with the same interface source and destination pair.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter    | Description                                                                      | Range   | Default |
+==============+==================================================================================+=========+=========+
| ipv4-address | Sets the address of tunnel's destination endpoint. The destination address must  | A.B.C.D | \-      |
|              | be a routable unicast IPv4 address.                                              |         |         |
+--------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# gre-tunnel-0
    dnRouter(cfg-if-gre-0)# destination 192.168.153.17


**Removing Configuration**

Destination-address is a mandatory configuration and cannot be removed, only changed.
::


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
