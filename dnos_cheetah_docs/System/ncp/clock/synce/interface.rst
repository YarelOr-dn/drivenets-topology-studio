system ncp clock synce interface
--------------------------------

**Minimum user role:** operator

Enter internal interface name

**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce

**Note**

- Notice the change in prompt.

**Parameter table**

+-----------+------------------------------------------+------------------+---------+
| Parameter | Description                              | Range            | Default |
+===========+==========================================+==================+=========+
| interface | Sets the internal source interface name. | | string         | \-      |
|           |                                          | | length 1-255   |         |
+-----------+------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# interface ge400-0/0/0
    dnRouter(cfg-system-ncp-7-clk-synce-ge400-0/0/0)#


**Removing Configuration**

Remove interface from internal interface list
::

    dnRouter(cfg-system-ncp-7-clk-synce)# no interface ge400-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
