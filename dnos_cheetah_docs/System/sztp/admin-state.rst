system sztp admin-state
-----------------------

**Minimum user role:** admin

To enable/disable SZTP.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system sztp

**Note**

- admin-state enabled will take place only after a reboot. admin-state disabled will take place immediately.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | controls whether SZTP bootstrapping is enabled or disabled. disabled state takes | | enabled    | disabled |
|             | effect immediately. enabled state takes effect after a restart                   | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-system-sztp)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
