protocols lacp interface system-id
----------------------------------

**Minimum user role:** operator

The interface's LACP system ID is formed by combining the interface priorityy with the interface system's ID. The system ID is the least significant part of the LACP system unique identifier, in the form of a MAC address. The NCR MAC address is randomly selected from a pool of addresses, whose first 3 bytes have a fixed value (84:40:76) and last 3 bytes are randomized on first start-up. The ID assignment is performed once after deployment and persists after reset. You can optionally change the system-ID.
To change the LACP system ID:

**Command syntax: system-id [system-id]**

**Command mode:** config

**Hierarchies**

- protocols lacp interface

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
    dnRouter(cfg-protocols-lacp)# interface bundle-2
    dnRouter(cfg-protocols-lacp-if)# system-id 11:22:33:44:55:66
    dnRouter(cfg-protocols-lacp-if)#


**Removing Configuration**

To revert to the global system-id:
::

    dnRouter(cfg-protocols-lacp-if)# no system-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
