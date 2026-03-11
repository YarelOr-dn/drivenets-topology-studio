system ncp clock ptp g8275-1 default-ds
---------------------------------------

**Minimum user role:** operator

Enter the PTP 1588v2 default dataset clock related configuration options.

To configure default dataset ptp clock parameters:

**Command syntax: default-ds**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp g8275-1

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# g8275-1
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# default-ds
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1-default-ds)#


**Removing Configuration**

To revert the ptp g8275.1 default dataset to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# no default-ds

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
