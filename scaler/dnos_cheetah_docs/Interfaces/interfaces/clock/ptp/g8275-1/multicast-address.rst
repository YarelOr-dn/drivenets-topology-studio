interfaces clock ptp g8275-1 multicast-address
----------------------------------------------

**Minimum user role:** operator

Set the PTP port destination MAC address for G.8275.1 as forwardable or non-forwardable.

**Command syntax: multicast-address [multicast-address]**

**Command mode:** config

**Hierarchies**

- interfaces clock ptp g8275-1

**Parameter table**

+-------------------+---------------------------------------+---------------------+-----------------+
| Parameter         | Description                           | Range               | Default         |
+===================+=======================================+=====================+=================+
| multicast-address | multicast address used as destination | | non-forwardable   | non-forwardable |
|                   |                                       | | forwardable       |                 |
+-------------------+---------------------------------------+---------------------+-----------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# ptp
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp)# g8275-1
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# multicast-address forwardable

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock ptp g8275-1 multicast-address forwardable


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# no multicast-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
