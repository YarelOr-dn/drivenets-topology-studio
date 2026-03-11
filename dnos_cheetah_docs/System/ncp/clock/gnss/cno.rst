system ncp clock gnss cno
-------------------------

**Minimum user role:** operator

Set the navigation carrier to noise density ratio [dbHz].

**Command syntax: cno [cno]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| cno       | GNSS CNO - ratio of the carrier power C to the noise power density N0, expressed | 0-255 | \-      |
|           | in dB-Hz                                                                         |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# cno 21


**Removing Configuration**

Reset CNo value to default.
::

    dnRouter(cfg-system-ncp-7-clk-gnss)# no cno

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
