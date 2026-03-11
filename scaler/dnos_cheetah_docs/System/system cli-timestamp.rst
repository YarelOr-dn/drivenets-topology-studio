system cli-timestamp
--------------------

**Minimum user role:** operator

By default, commands displayed in the CLI do not show a timestamp. To turn on timestamp so that each entered command will be displayed with a timestamp:

**Command syntax: cli-timestamp [admin-state]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- In the same way as debug set commands, the command "set cli-timestamp" overrides this configuration during the session.

- no command returns to default configuration.

**Parameter table**

+-------------+---------------------------------------------------+--------------+----------+
| Parameter   | Description                                       | Range        | Default  |
+=============+===================================================+==============+==========+
| admin-state | The desired configuration of cli-timestamp option | | enabled    | disabled |
|             |                                                   | | disabled   |          |
+-------------+---------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cli-timestamp enabled
    dnRouter(cfg-system)# cli-timestamp disabled


**Removing Configuration**

To revert the system cli-timestamp to its default value:
::

    dnRouter(cfg-system)# no cli-timestamp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
