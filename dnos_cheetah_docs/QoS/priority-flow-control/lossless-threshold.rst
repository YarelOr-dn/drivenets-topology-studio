qos priority-flow-control lossless-pause-threshold lossless-clear-threshold
---------------------------------------------------------------------------

**Minimum user role:** operator

When the size of a global-VSQ exceeds the PFC pause threshold (in percentages), PFC pause frames are sent to all PFC enabled peers until the global-VSQ size falls below the lossless-clear threshold.

**Command syntax: lossless-pause-threshold [lossless-pause-threshold] lossless-clear-threshold [lossless-clear-threshold]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Note**

- There are no default values because the values depend on HBM/SRAM size and states that may vary between installations and devices.

- This command is only active after setting pause-threshold and clear-threshold.

- This command is only active after it was configured even if the priority-flow-control admin-state is enabled.

- When configured, priority-flow-control admin-state enables and disables this command without loosing the configured values.

**Parameter table**

+--------------------------+-------------+-------+---------+
| Parameter                | Description | Range | Default |
+==========================+=============+=======+=========+
| lossless-pause-threshold | percentage  | 0-100 | \-      |
+--------------------------+-------------+-------+---------+
| lossless-clear-threshold | percentage  | 1-100 | \-      |
+--------------------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# lossless-pause-threshold 10 lossless-clear-threshold 11
    dnRouter(cfg-qos-pfc)#


**Removing Configuration**

To remove the command:
::

    dnRouter(cfg-qos-pfc)# no lossless-pause-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
