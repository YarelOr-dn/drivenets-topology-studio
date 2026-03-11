protocols msdp default-peer
---------------------------

**Minimum user role:** operator

A default peer is an MSDP peer from which all MSDP SA messages are accepted. You can use this command to define a MSDP default-peer and enter its configuration.

**Command syntax: default-peer [default-peer]**

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
- Default-peer config will not pass commit unless the mandatory "remote-as" configuration is applied

- Default-peer address must be unique for all msdp groups or default-peers.

**Parameter table**

+--------------+--------------------------+---------+---------+
| Parameter    | Description              | Range   | Default |
+==============+==========================+=========+=========+
| default-peer | Set an MSDP default-peer | A.B.C.D | \-      |
+--------------+--------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 121.17.4.1
    dnRouter(cfg-protocols-msdp-default-peer)#


**Removing Configuration**

To remove the default-peer configuration:
::

    dnRouter(cfg-protocols-msdp)# no default-peer 121.17.4.1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
