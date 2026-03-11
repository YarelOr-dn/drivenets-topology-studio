protocols ospf instance area interface network-type
---------------------------------------------------

**Minimum user role:** operator

Set OSPF area interface network type.

**Command syntax: network-type [network]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**
- 'no network-type' command sets the network to its default value - point-to-point.

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
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# network-type point-to-point


**Removing Configuration**

To return network-type to its default value:
::

    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospf-area-if)# no network-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
