system ncp clock gnss constellations beidou
-------------------------------------------

**Minimum user role:** operator

Set the BEIDOU constellation as enabled or disabled.

**Command syntax: beidou [beidou]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss constellations

**Parameter table**

+-----------+---------------------------------------------------+--------------+----------+
| Parameter | Description                                       | Range        | Default  |
+===========+===================================================+==============+==========+
| beidou    | Sets BEIDOU constellation as enabled or disabled. | | disabled   | disabled |
|           |                                                   | | enabled    |          |
+-----------+---------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# constellations
    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# beidou enabled


**Removing Configuration**

To disable the BEIDOU constellation
::

    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# no beidou

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
