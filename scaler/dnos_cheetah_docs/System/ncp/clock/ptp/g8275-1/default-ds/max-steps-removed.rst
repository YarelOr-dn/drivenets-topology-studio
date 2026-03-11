system ncp clock ptp g8275-1 default-ds max-steps-removed
---------------------------------------------------------

**Minimum user role:** operator

Set the PTP clock max-steps-removed attribute.

**Command syntax: max-steps-removed [max-steps-removed]**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp g8275-1 default-ds

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter         | Description                                                                      | Range | Default |
+===================+==================================================================================+=======+=========+
| max-steps-removed | Limits clock qualification when steps-removed field in the announce message      | 1-255 | 20      |
|                   | exceeds this value.                                                              |       |         |
+-------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# g8275-1
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# default-ds
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)# max-steps-removed 20


**Removing Configuration**

To revert max-steps-removed value to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)# no max-steps-removed

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
