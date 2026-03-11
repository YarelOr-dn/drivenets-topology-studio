interfaces clock synce
----------------------

**Minimum user role:** operator

Enter interface level Synchronous-Ethernet related configuration options and settings.

**Command syntax: synce**

**Command mode:** config

**Hierarchies**

- interfaces clock

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# synce
    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock synce


**Removing Configuration**

To revert the interface sync-ethernet to its default value:
::

    dnRouter(cfg-if-ge400-0/0/0-clk)# no synce

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
