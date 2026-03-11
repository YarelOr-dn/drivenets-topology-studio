system alarms max-alarm-history
-------------------------------

**Minimum user role:** operator

Configures the maximum amount of alarms that will be stored per resource in the alarms history.

**Command syntax: max-alarm-history [max-alarm-history]**

**Command mode:** config

**Hierarchies**

- system alarms

**Note**

- Reducing this number might impact the alarms history, in case there are more alarm occurances that will be configured with the new value, the oldest alarms will be deleted.

- increasing the number won't case alarms deletion.

- Setting the alarms history to 0, will disable alarms history support.

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter         | Description                                                                      | Range | Default |
+===================+==================================================================================+=======+=========+
| max-alarm-history | Specifies the maximum amount of alarms that will be stored per resource in the   | 0-100 | 1       |
|                   | alarms history.                                                                  |       |         |
+-------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# max-alarm-history 32


**Removing Configuration**

To revert max-alarm-history to default:
::

    dnRouter(cfg-system-alarms)# no max-alarm-history

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
