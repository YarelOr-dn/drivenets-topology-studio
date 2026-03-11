interfaces clock ptp
--------------------

**Minimum user role:** operator

Enter PTP 1588v2 port specific related configuration options and reference synchronization clock settings.

To configure ptp per-port parameters:

**Command syntax: ptp**

**Command mode:** config

**Hierarchies**

- interfaces clock

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# ptp


**Removing Configuration**

Remove ptp port configuration from the interface:
::

    dnRouter(cfg-if-ge400-0/0/0-clk) no ptp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
