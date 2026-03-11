system ncp clock ptp tod-mode
-----------------------------

**Minimum user role:** operator

Set Tod RJ45 port as input or output.

**Command syntax: tod-mode [tod-mode]**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp

**Note**
- The command is applicable only to UfiSpace NCPL platform.

**Parameter table**

+-----------+---------------------------------------------------------+------------+---------+
| Parameter | Description                                             | Range      | Default |
+===========+=========================================================+============+=========+
| tod-mode  | Indicate whether the ToD port is set as input or output | | output   | output  |
|           |                                                         | | input    |         |
+-----------+---------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# tod-mode input


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-system-ncp-7-clk-ptp)# no tod-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
