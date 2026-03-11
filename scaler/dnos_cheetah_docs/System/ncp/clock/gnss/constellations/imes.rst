system ncp clock gnss constellations imes
-----------------------------------------

**Minimum user role:** operator

Set the IMES constellation as enabled or disabled.

**Command syntax: imes [imes]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss constellations

**Parameter table**

+-----------+-------------------------------------------------+--------------+----------+
| Parameter | Description                                     | Range        | Default  |
+===========+=================================================+==============+==========+
| imes      | Sets IMES constellation as enabled or disabled. | | disabled   | disabled |
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
    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# imes enabled


**Removing Configuration**

To disable the IMES constellation
::

    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# no imes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
