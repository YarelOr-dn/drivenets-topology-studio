interfaces clock ptp g8275-1 announce-receipt-timeout
-----------------------------------------------------

**Minimum user role:** operator

Set the PTP per-port announce receipt timeout attribute.

**Command syntax: announce-receipt-timeout [announce-receipt-timeout]**

**Command mode:** config

**Hierarchies**

- interfaces clock ptp g8275-1

**Parameter table**

+--------------------------+-----------------------------------------+-------+---------+
| Parameter                | Description                             | Range | Default |
+==========================+=========================================+=======+=========+
| announce-receipt-timeout | PTP clock port announce-receipt-timeout | 3-10  | 3       |
+--------------------------+-----------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# ptp
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp)# g8275-1
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# announce-receipt-timeout 3

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock ptp g8275-1 announce-receipt-timeout 3


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# no announce-receipt-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
