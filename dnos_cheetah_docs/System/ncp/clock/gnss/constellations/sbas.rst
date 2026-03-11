system ncp clock gnss constellations sbas
-----------------------------------------

**Minimum user role:** operator

Set the SBAS constellation as enabled or disabled.

**Command syntax: sbas [sbas]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss constellations

**Parameter table**

+-----------+-------------------------------------------------+--------------+----------+
| Parameter | Description                                     | Range        | Default  |
+===========+=================================================+==============+==========+
| sbas      | Sets SBAS constellation as enabled or disabled. | | disabled   | disabled |
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
    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# sbas enabled


**Removing Configuration**

To disable the SBAS constellation
::

    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# no sbas

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
