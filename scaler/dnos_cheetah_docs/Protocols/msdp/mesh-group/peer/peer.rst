protocols msdp mesh-group peer
------------------------------

**Minimum user role:** operator

You can use this command to define a MSDP mesh-group peer address and enter its configuration.

**Command syntax: peer [peer]**

**Command mode:** config

**Hierarchies**

- protocols msdp mesh-group

**Note**
- The mesh group peer address must be unique throughout all MSDP mesh-groups and default-peer members.

**Parameter table**

+-----------+--------------------------------+---------+---------+
| Parameter | Description                    | Range   | Default |
+===========+================================+=========+=========+
| peer      | set the MSDP peer IPv4 address | A.B.C.D | \-      |
+-----------+--------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)# peer 2.3.4.5
    dnRouter(cfg-protocols-msdp-group-peer)#


**Removing Configuration**

To remove the peer from the mesh-group:
::

    dnRouter(cfg-protocols-msdp-group)# no peer 2.3.4.5

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
