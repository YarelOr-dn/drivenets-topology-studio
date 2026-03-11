protocols ospfv3 area interface bfd min-tx
------------------------------------------

**Minimum user role:** operator

To set the OSPFv3 BFD minimum transmit interval for the interface:

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area interface bfd

**Note**
- The 'no' command returns to the default settings.

**Parameter table**

+-----------+-------------------------------------------------------+--------+---------+
| Parameter | Description                                           | Range  | Default |
+===========+=======================================================+========+=========+
| min-tx    | set desired minimum transmit interval for BFD session | 5-1700 | \-      |
+-----------+-------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if)# bfd
    dnRouter(cfg-ospfv3-area-if-bfd)# min-tx 400


**Removing Configuration**

To return the min-tx interval to its default value: 
::

    dnRouter(cfg-ospfv3-area-if-bfd)# no min-tx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
