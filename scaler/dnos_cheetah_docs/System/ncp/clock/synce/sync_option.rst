system ncp clock synce sync-option
----------------------------------

**Minimum user role:** operator

Set the syncE clock synchronization option.

**Command syntax: sync-option [option]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce

**Parameter table**

+-----------+----------------------------------------------+--------------+----------+
| Parameter | Description                                  | Range        | Default  |
+===========+==============================================+==============+==========+
| option    | Sets the syncE clock synchronization option. | | option-1   | option-1 |
|           |                                              | | option-2   |          |
+-----------+----------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# sync-option option-1


**Removing Configuration**

To revert the sync-option to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-synce)# no sync-option

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
