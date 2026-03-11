interfaces clock synce mode
---------------------------

**Minimum user role:** operator

When Sync-Ethernet timing feature is enabled, each ethernet port shall be set to either synchronous or non-synchronous.

**Command syntax: mode [mode]**

**Command mode:** config

**Hierarchies**

- interfaces clock synce

**Note**

- This command is currently applicable only to physical 400G and breakout interfaces on UfiSpace NCP3 platforms or physical 10G and 100G interfaces on ufiSpace NCPL platforms.

**Parameter table**

+-----------+---------------------------------------------+---------------------+-----------------+
| Parameter | Description                                 | Range               | Default         |
+===========+=============================================+=====================+=================+
| mode      | The interface sync-ethernet operating mode. | | synchronous       | non-synchronous |
|           |                                             | | non-synchronous   |                 |
+-----------+---------------------------------------------+---------------------+-----------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# synce
    dnRouter(cfg-if-ge400-0/0/0-clk-synce)# mode synchronous

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock synce mode non-synchronous


**Removing Configuration**

To set interface synce mode to default:
::

    dnRouter(cfg-if-ge400-0/0/0-clk-synce)# no mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
