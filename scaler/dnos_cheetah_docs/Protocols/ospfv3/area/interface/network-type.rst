protocols ospfv3 area interface network-type
--------------------------------------------

**Minimum user role:** operator

Set the OSPF area interface network type.

**Command syntax: network-type [network]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area interface

**Note**
- The 'no network-type' command sets the network to its default value - point-to-point.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+----------------+----------------+
| Parameter | Description                                                                      | Range          | Default        |
+===========+==================================================================================+================+================+
| network   | Enables OSPF on an interface and set enters interface ospf parameters            | point-to-point | point-to-point |
|           | configuration                                                                    |                |                |
+-----------+----------------------------------------------------------------------------------+----------------+----------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if)# network-type point-to-point


**Removing Configuration**

To return network-type to its default value:
::

    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospfv3-area-if)# no network-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
