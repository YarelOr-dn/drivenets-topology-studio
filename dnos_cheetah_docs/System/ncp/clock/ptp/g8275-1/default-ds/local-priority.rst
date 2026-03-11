system ncp clock ptp g8275-1 default-ds local-priority
------------------------------------------------------

**Minimum user role:** operator

Set the PTP clock local-priority attribute.

**Command syntax: local-priority [local-priority]**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp g8275-1 default-ds

**Parameter table**

+----------------+------------------------------+-------+---------+
| Parameter      | Description                  | Range | Default |
+================+==============================+=======+=========+
| local-priority | Set PTP clock local-priority | 0-255 | 128     |
+----------------+------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# g8275-1
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# default-ds
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)# local-priority 128


**Removing Configuration**

To revert local-priority value to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)# no local-priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
