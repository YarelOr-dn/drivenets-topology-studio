qos priority-flow-control global-traffic-class global-clear-threshold
---------------------------------------------------------------------

**Minimum user role:** operator

If the VSQ size for a particular queue is less than the global-clear-threshold value the transmission of PFC pause frames stops. Lower hierarchies use global thresholds unless they have their own specific configuration. To configure the PFC global-clear-threshold for a specific traffic class for all interfaces:

**Command syntax: global-clear-threshold [global-clear-threshold] [units]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control global-traffic-class

**Note**

- The default clear-threshold is 80kbytes. An explicit configuration under a certain traffic class takes precedence over the inherited global configuration.

- The global-clear-threshold must be lower than the global-pause-threshold or the traffic class specific pause-threshold.

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter              | Description                                                                      | Range       | Default |
+========================+==================================================================================+=============+=========+
| global-clear-threshold | The PFC clear-threshold value is the VSQ size to stop sending pause frames for a | 0-199999744 | \-      |
|                        | specific traffic class.                                                          |             |         |
+------------------------+----------------------------------------------------------------------------------+-------------+---------+
| units                  |                                                                                  | | bytes     | bytes   |
|                        |                                                                                  | | kbytes    |         |
|                        |                                                                                  | | mbytes    |         |
+------------------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# traffic-class 3
    dnRouter(cfg-qos-pfc-tc3)# global-clear-threshold 100 kbytes


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-qos-pfc-tc3)# no clear-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
