system ncp clock synce
----------------------

**Minimum user role:** operator

Enter Synchronous-Ethernet related configuration options and reference synchronization clock settings.

To configure synce parameters:

**Command syntax: synce**

**Command mode:** config

**Hierarchies**

- system ncp clock

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk/synce)#


**Removing Configuration**

To revert the sync-ethernet option to its default value:
::

    dnRouter(cfg-system-ncp-7-clk)# no synce

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
