system ncp clock gnss constellations galileo
--------------------------------------------

**Minimum user role:** operator

Set the GALILEO constellation as enabled or disabled.

**Command syntax: galileo [galileo]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss constellations

**Parameter table**

+-----------+----------------------------------------------------+--------------+----------+
| Parameter | Description                                        | Range        | Default  |
+===========+====================================================+==============+==========+
| galileo   | Sets GALILEO constellation as enabled or disabled. | | disabled   | disabled |
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
    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# galileo enabled


**Removing Configuration**

To disable the GALILEO constellation
::

    dnRouter(cfg-system-ncp-7-clk-gnss-constellations)# no galileo

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
