system ncp clock synce interface holdoff
----------------------------------------

**Minimum user role:** operator

Set internal reference source hold-off-time parameter.

**Command syntax: holdoff [hold-off-time]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce interface

**Parameter table**

+---------------+--------------------+----------+---------+
| Parameter     | Description        | Range    | Default |
+===============+====================+==========+=========+
| hold-off-time | SyncE holdoff time | 300-1800 | 300     |
+---------------+--------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# interface ge400-0/0/0
    dnRouter(cfg-system-ncp-7-clk-synce-ge400-0/0/0)# holdoff 400


**Removing Configuration**

To revert the internal reference source to default hold-off time:
::

    dnRouter(cfg-system-ncp-7-clk-synce-ge400-0/0/0)# no holdoff

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
