protocols isis instance interface bfd min-tx
--------------------------------------------

**Minimum user role:** operator

The minimum transmission interval is the time between consecutive transmissions of BFD packets. To configure the transmission rate of BFD packets:

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface bfd

**Note**

- Due to hardware limitation, maximum supported transmit rate is 1700msec, and negotiated transmit interval higher than 1700 msec will result in actual transmit rate of 1700 msec.

**Parameter table**

+-----------+--------------------------------------------------------------+--------+---------+
| Parameter | Description                                                  | Range  | Default |
+===========+==============================================================+========+=========+
| min-tx    | The interval (in msec) between transmissions of BFD packets. | 5-1700 | 300     |
+-----------+--------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# isis-level level-1-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# bfd
    dnRouter(cfg-inst-if-bfd)# min-tx 50


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-if-bfd)# no min-tx

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 12.0    | Command introduced               |
+---------+----------------------------------+
| 15.1    | Added support for 5msec interval |
+---------+----------------------------------+
