system ncp clock gnss 10mhz mode
--------------------------------

**Minimum user role:** operator

When Sync-Ethernet timing feature is enabled, the GNSS based 10MHz port is set to either synchronous or non-synchronous.

**Command syntax: mode [mode]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss 10mhz

**Parameter table**

+-----------+----------------------------------------------+---------------------+-----------------+
| Parameter | Description                                  | Range               | Default         |
+===========+==============================================+=====================+=================+
| mode      | The GNSS 10MHz sync-ethernet operating mode. | | synchronous       | non-synchronous |
|           |                                              | | non-synchronous   |                 |
+-----------+----------------------------------------------+---------------------+-----------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# 10mhz
    dnRouter(cfg-system-ncp-7-clk-gnss-10mhz)# mode synchronous

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock synce mode non-synchronous


**Removing Configuration**

To set interface synce mode to default:
::

    dnRouter(cfg-system-ncp-7-clk-gnss-10mhz)# no mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
