system ncp clock synce interface priority
-----------------------------------------

**Minimum user role:** operator

Set internal reference source priority.

**Command syntax: priority [priority]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce interface

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
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# interface ge400-0/0/0
    dnRouter(cfg-system-ncp-7-clk-synce-ge400-0/0/0)# priority 1


**Removing Configuration**

To revert the source priority to default values:
::

    dnRouter(cfg-system-ncp-7-clk-synce-ge400-0/0/0)# no priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
