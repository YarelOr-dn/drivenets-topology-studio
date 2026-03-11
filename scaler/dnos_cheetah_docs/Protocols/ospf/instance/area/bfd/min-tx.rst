protocols ospf instance area bfd min-tx
---------------------------------------

**Minimum user role:** operator

To set the OSPF BFD minimum transmit interval for the interface:

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area bfd

**Note**
- Due to hardware limitation, maximum supported transmit rate is 1700msec, and negotiated transmit interval higher than 1700msec will result in actual transmit rate of 1700msec.
- 'no' command returns to default settings

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
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-ospf-area)# bfd
    dnRouter(cfg-ospf-area-bfd)# min-tx 400


**Removing Configuration**

To return the min-tx interval to its default value: 
::

    dnRouter(cfg-ospf-area-bfd)# no min-tx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
