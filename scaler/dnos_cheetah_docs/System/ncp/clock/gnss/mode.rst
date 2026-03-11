system ncp clock gnss mode
--------------------------

**Minimum user role:** operator

Set the GNSS port as enabled or disabled.

**Command syntax: mode [mode]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss

**Parameter table**

+-----------+----------------------------------------+--------------+----------+
| Parameter | Description                            | Range        | Default  |
+===========+========================================+==============+==========+
| mode      | Sets GNSS port as enabled or disabled. | | enabled    | disabled |
|           |                                        | | disabled   |          |
+-----------+----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# mode enabled


**Removing Configuration**

To disable the GNSS port
::

    dnRouter(cfg-system-ncp-7-clk-gnss)# no gnss

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
