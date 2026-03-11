system ncp clock synce interface wtr
------------------------------------

**Minimum user role:** operator

Set internal reference source wait-to-restore time.

**Command syntax: wtr [wtr]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce interface

**Parameter table**

+-----------+-------------------------------------------+-------+---------+
| Parameter | Description                               | Range | Default |
+===========+===========================================+=======+=========+
| wtr       | Sets the wait to restore time in minutes. | 0-12  | 5       |
+-----------+-------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# interface ge400-0/0/0
    dnRouter(cfg-system-ncp-7-clk-synce-ge400-0/0/0)# wtr 5


**Removing Configuration**

To revert the source wtr time to default values:
::

    dnRouter(cfg-system-ncp-7-clk-synce-ge400-0/0/0)# no wtr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
