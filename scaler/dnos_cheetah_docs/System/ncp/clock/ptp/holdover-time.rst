system ncp clock ptp holdover-time
----------------------------------

**Minimum user role:** operator

Set the PTP clock holdover-time attribute.

**Command syntax: holdover-time [holdover-time]**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp

**Parameter table**

+---------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter     | Description                                                                      | Range  | Default |
+===============+==================================================================================+========+=========+
| holdover-time | The duration time that a clock stays in holdover-in-spec before changing to      | 0-1440 | 120     |
|               | holdover-out-spec identity.                                                      |        |         |
+---------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# holdover-time 120


**Removing Configuration**

To revert holdover-time value to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-ptp)# no holdover-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
