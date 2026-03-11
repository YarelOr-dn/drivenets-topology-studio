system ncp clock ptp g8275-1 default-ds priority2
-------------------------------------------------

**Minimum user role:** operator

Set the PTP clock priority2 attribute.

**Command syntax: priority2 [priority2]**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp g8275-1 default-ds

**Parameter table**

+-----------+---------------------------------+-------+---------+
| Parameter | Description                     | Range | Default |
+===========+=================================+=======+=========+
| priority2 | Irrelevant for T-TSC clock-type | 0-255 | 128     |
+-----------+---------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# g8275-1
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# default-ds
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)# priority2 128


**Removing Configuration**

To revert priority2 value to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)# no priority2

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
