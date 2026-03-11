qos priority-flow-control lossy-threshold
-----------------------------------------

**Minimum user role:** operator

When the lossy global VSQ size is above the lossy-threshold value, lossy packets are dropped. To configure the lossy global VSQ size threshold:

**Command syntax: lossy-threshold [lossy-threshold]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Note**

- This command has no defaults.

- This command is only active once the threshold is set.

- This command is active ONLY after it has been configured even if the priority-flow-control admin-state is enabled.

- When configured, priority-flow-control admin-state enables and disables this command without loosing the configured values.

- When a lossy threshold is triggered, tail-drop will apply to all interfaces on all traffic-classes except traffic-classes that are set as lossless on all interfaces.

**Parameter table**

+-----------------+-------------+-------+---------+
| Parameter       | Description | Range | Default |
+=================+=============+=======+=========+
| lossy-threshold | percentage  | 0-100 | \-      |
+-----------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# lossy-threshold 10


**Removing Configuration**

To remove the command:
::

    dnRouter(cfg-qos-pfc)# no lossy-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
