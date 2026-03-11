protocols lacp system-id
------------------------

**Minimum user role:** operator

The LACP system ID is formed by combining the LACP system-priority with the system's ID. The system ID is the least significant part of the LACP system unique identifier, in the form of a MAC address. The NCR MAC address is randomly selected from a pool of addresses, whose first 3 bytes have a fixed value (84:40:76) and last 3 bytes are randomized on first start-up. The ID assignment is performed once after deployment and persists after reset. You can optionally change the system-id.
To change the LACP system ID:

**Command syntax: system-id [system-id]**

**Command mode:** config

**Hierarchies**

- protocols lacp

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| system-id | The MAC address portion of the node's System ID. This is combined with the       | \-    | \-      |
|           | system priority to construct the 8-octet system-id                               |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)# system-id 11:22:33:44:55:66


**Removing Configuration**

To revert to the default system-id:
::

    dnRouter(cfg-protocols-lacp)# no system-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
