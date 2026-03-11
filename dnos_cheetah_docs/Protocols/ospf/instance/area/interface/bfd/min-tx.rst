protocols ospf instance area interface bfd min-tx
-------------------------------------------------

**Minimum user role:** operator

To set the OSPF BFD minimum transmit interval for the interface:

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface bfd

**Note**
- 'no' command returns to default settings

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
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# bfd
    dnRouter(cfg-ospf-area-if-bfd)# min-tx 400


**Removing Configuration**

To return the min-tx interval to its default value: 
::

    dnRouter(cfg-ospf-area-if-bfd)# no min-tx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
