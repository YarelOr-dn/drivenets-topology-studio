system ncp clock gnss 10mhz priority
------------------------------------

**Minimum user role:** operator

Set the 10mhz GNSS reference source priority.

**Command syntax: priority [priority]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss 10mhz

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| priority  | Indicates the configured priority of the source clock. A smaller value           | 0-255 | 0       |
|           | represents a higher priority. 0 means interface will not be included for clock   |       |         |
|           | selection                                                                        |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# 10mhz
    dnRouter(cfg-system-ncp-7-clk-gnss-10mhz)# priority 1


**Removing Configuration**

To revert the 10mhz GNSS source priority to default values:
::

    dnRouter(cfg-system-ncp-7-clk-gnss-10mhz)# no priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
