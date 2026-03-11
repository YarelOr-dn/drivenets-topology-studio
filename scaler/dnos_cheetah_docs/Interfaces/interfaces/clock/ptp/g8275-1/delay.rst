interfaces clock ptp g8275-1 delay
----------------------------------

**Minimum user role:** operator

Set the PTP per-port delay attribute.

**Command syntax: delay [delay]**

**Command mode:** config

**Hierarchies**

- interfaces clock ptp g8275-1

**Parameter table**

+-----------+----------------------------------------------------------------------------------+----------------+---------+
| Parameter | Description                                                                      | Range          | Default |
+===========+==================================================================================+================+=========+
| delay     | The additional delay in nSec to compensate for asymmetrical upstream and         | -100000-100000 | 0       |
|           | downstream delays.                                                               |                |         |
+-----------+----------------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# ptp
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp)# g8275-1
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# delay 1

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock ptp g8275-1 delay 1


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# no delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
