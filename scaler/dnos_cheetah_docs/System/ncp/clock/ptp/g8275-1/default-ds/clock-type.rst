system ncp clock ptp g8275-1 default-ds clock-type
--------------------------------------------------

**Minimum user role:** operator

Set the PTP clock type.

**Command syntax: clock-type [clock-type]**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp g8275-1 default-ds

**Parameter table**

+------------+--------------------------+-----------+---------+
| Parameter  | Description              | Range     | Default |
+============+==========================+===========+=========+
| clock-type | Sets the PTP clock type. | | t-gm    | t-bc    |
|            |                          | | t-bc    |         |
|            |                          | | t-tsc   |         |
+------------+--------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# g8275-1
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# default-ds
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)# clock-type t-bc


**Removing Configuration**

To revert clock-type to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)# no clock-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
