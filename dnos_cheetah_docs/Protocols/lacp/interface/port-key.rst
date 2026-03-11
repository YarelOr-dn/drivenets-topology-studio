protocols lacp interface port-key
---------------------------------

**Minimum user role:** operator

The Port-key (2 bytes) of this bundle interface.

**Command syntax: port-key [port-key]**

**Command mode:** config

**Hierarchies**

- protocols lacp interface

**Parameter table**

+-----------+--------------------------------------------------+---------+---------+
| Parameter | Description                                      | Range   | Default |
+===========+==================================================+=========+=========+
| port-key  | Port-Key used by the node on this LAG interface. | 0-65535 | \-      |
+-----------+--------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)# interface bundle-2
    dnRouter(cfg-protocols-lacp-if)# port-key 10
    dnRouter(cfg-protocols-lacp-if)#


**Removing Configuration**

To revert the port-key to the global value.
::

    dnRouter(cfg-protocols-lacp-if)# no port-key

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
