interfaces source
-----------------

**Minimum user role:** operator

To configure the tunnel's source endpoint:

**Command syntax: source [source-address]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the gre-tunnel interface.

- You cannot create multiple GRE tunnels with the same interface source and destination pair.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                                      | Range   | Default |
+================+==================================================================================+=========+=========+
| source-address | Sets the address of tunnel's source endpoint. The source address must be an      | A.B.C.D | \-      |
|                | existing local address in the same VRF.                                          |         |         |
+----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# gre-tunnel-0
    dnRouter(cfg-if-gre-0)# source 1.1.1.1


**Removing Configuration**

Source-address is a mandatory configuration and cannot be removed, only changed.
::


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
