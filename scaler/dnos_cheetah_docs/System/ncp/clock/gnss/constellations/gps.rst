system ncp clock gnss constellations gps
----------------------------------------

**Minimum user role:** operator

Set the GPS constellation as enabled or disabled.

**Command syntax: gps [gps]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss constellations

**Parameter table**

+-----------+------------------------------------------------+--------------+----------+
| Parameter | Description                                    | Range        | Default  |
+===========+================================================+==============+==========+
| gps       | Sets GPS constellation as enabled or disabled. | | disabled   | disabled |
|           |                                                | | enabled    |          |
+-----------+------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# constellations
    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# gps enabled


**Removing Configuration**

To disable the GPS constellation
::

    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# no gps

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
