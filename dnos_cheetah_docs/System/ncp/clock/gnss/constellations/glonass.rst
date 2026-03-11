system ncp clock gnss constellations glonass
--------------------------------------------

**Minimum user role:** operator

Set the GLONASS constellation as enabled or disabled.

**Command syntax: glonass [glonass]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss constellations

**Parameter table**

+-----------+----------------------------------------------------+--------------+----------+
| Parameter | Description                                        | Range        | Default  |
+===========+====================================================+==============+==========+
| glonass   | Sets GLONASS constellation as enabled or disabled. | | disabled   | disabled |
|           |                                                    | | enabled    |          |
+-----------+----------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# constellations
    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# glonass enabled


**Removing Configuration**

To disable the GLONASS constellation
::

    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# no glonass

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
