qos priority-flow-control global-clear-threshold
------------------------------------------------

**Minimum user role:** operator

If VSQ size for a particular queue is less than the clear-threshold value, the transmission of PFC pause frames will be stopped. Lower hierarchies use global thresholds unless they have their own specific configuration. To configure the global PFC clear threshold on the interface that shall apply for each traffic class:

**Command syntax: global-clear-threshold [global-clear-threshold] [units]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Note**

- Default clear-threshold is 80kbytes. An explicit configuration for a specific traffic class takes precendence over the inherited global configuration.

- Clear-threshold must be lower than the global pause-threshold or the traffic class specific pause-threshold

**Parameter table**

+------------------------+-----------------------------------------------------------------------------+-------------+---------+
| Parameter              | Description                                                                 | Range       | Default |
+========================+=============================================================================+=============+=========+
| global-clear-threshold | The PFC clear-threshold value is the VSQ size to stop sending pause frames. | 0-199999744 | 80000   |
+------------------------+-----------------------------------------------------------------------------+-------------+---------+
| units                  |                                                                             | | bytes     | bytes   |
|                        |                                                                             | | kbytes    |         |
|                        |                                                                             | | mbytes    |         |
+------------------------+-----------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# global-clear-threshold 100 kbytes


**Removing Configuration**

To revert to the default value
::

    dnRouter(cfg-qos-pfc)# no clear-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
