interfaces clock ptp g8275-1 admin-state
----------------------------------------

**Minimum user role:** operator

Enable or disable the PTP port.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces clock ptp g8275-1

**Parameter table**

+-------------+-------------------------------------------+--------------+----------+
| Parameter   | Description                               | Range        | Default  |
+=============+===========================================+==============+==========+
| admin-state | enable PTP port functionality or reset it | | enabled    | disabled |
|             |                                           | | disabled   |          |
+-------------+-------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# ptp
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp)# g8275-1
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock ptp g8275-1 admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
