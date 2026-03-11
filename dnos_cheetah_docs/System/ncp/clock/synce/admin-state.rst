system ncp clock synce admin-state
----------------------------------

**Minimum user role:** operator

Enable or disable synchronous ethernet feature.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce

**Parameter table**

+-------------+---------------------------------------+--------------+----------+
| Parameter   | Description                           | Range        | Default  |
+=============+=======================================+==============+==========+
| admin-state | Sets the sync-ethernet feature state. | | disabled   | disabled |
|             |                                       | | enabled    |          |
+-------------+---------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# admin-state enabled


**Removing Configuration**

To revert the admin-state to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-synce)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
