system alarms max-boot-delay
----------------------------

**Minimum user role:** operator

To configure the maximum system boot delay before the alarm monitoring starts.

**Command syntax: max-boot-delay [max-boot-delay]**

**Command mode:** config

**Hierarchies**

- system alarms

**Note**

- Alarms conditions will be verified after the max-boot-delay time, the time units are in seconds.

- This delay will be applied after system restart/upgrade, in case the alarms admin-state is enabled.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter      | Description                                                                      | Range     | Default |
+================+==================================================================================+===========+=========+
| max-boot-delay | Specifies the maximum time that alarms engine will wait before starting the      | 100-18000 | 300     |
|                | monitoring after system boot, in seconds.                                        |           |         |
+----------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# max-boot-delay 300


**Removing Configuration**

To revert max-boot-delay to default:
::

    dnRouter(cfg-system-alarms)# no max-boot-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
