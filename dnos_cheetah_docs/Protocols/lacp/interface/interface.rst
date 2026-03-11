protocols lacp interface
------------------------

**Minimum user role:** operator

Configure the interface under the LACP protocol.

**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- protocols lacp

**Parameter table**

+-----------+---------------------------+------------------+---------+
| Parameter | Description               | Range            | Default |
+===========+===========================+==================+=========+
| interface | Reference to the list key | | string         | \-      |
|           |                           | | length 1-255   |         |
+-----------+---------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)# interface bundle-2
    dnRouter(cfg-protocols-lacp-if)#


**Removing Configuration**

To remove the interface from the lacp:
::

    dnRouter(cfg-protocols-lacp)# no interface bundle-2

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
