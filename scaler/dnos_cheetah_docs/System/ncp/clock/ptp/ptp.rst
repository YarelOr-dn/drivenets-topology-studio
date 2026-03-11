system ncp clock ptp
--------------------

**Minimum user role:** operator

Enter PTP 1588v2 related configuration options and reference synchronization clock settings.

To configure ptp parameters:

**Command syntax: ptp**

**Command mode:** config

**Hierarchies**

- system ncp clock

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)#


**Removing Configuration**

To revert ptp config to its default value:
::

    dnRouter(cfg-system-ncp-7-clk)# no ptp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
