system ncp clock gnss constellations qzss
-----------------------------------------

**Minimum user role:** operator

Set the QZSS constellation as enabled or disabled.

**Command syntax: qzss [qzss]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss constellations

**Parameter table**

+-----------+-------------------------------------------------+--------------+----------+
| Parameter | Description                                     | Range        | Default  |
+===========+=================================================+==============+==========+
| qzss      | Sets QZSS constellation as enabled or disabled. | | disabled   | disabled |
|           |                                                 | | enabled    |          |
+-----------+-------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# constellations
    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# qzss enabled


**Removing Configuration**

To disable the QZSS constellation
::

    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# no qzss

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
