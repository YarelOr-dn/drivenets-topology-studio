protocols ospfv3 area bfd min-tx
--------------------------------

**Minimum user role:** operator

To set the OSPFv3 BFD default minimum transmit interval for the area:

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area bfd

**Note**
- The 'no' command returns to the default settings.

**Parameter table**

+-----------+-------------------------------------------------------+--------+---------+
| Parameter | Description                                           | Range  | Default |
+===========+=======================================================+========+=========+
| min-tx    | set desired minimum transmit interval for BFD session | 5-1700 | 300     |
+-----------+-------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-ospfv3-area)# bfd
    dnRouter(cfg-ospfv3-area-bfd)# min-tx 400


**Removing Configuration**

To return the min-tx interval to its default value: 
::

    dnRouter(cfg-ospfv3-area-bfd)# no min-tx

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 11.6    | Command introduced                |
+---------+-----------------------------------+
| 15.1    | Added support for 5msec interval  |
+---------+-----------------------------------+
