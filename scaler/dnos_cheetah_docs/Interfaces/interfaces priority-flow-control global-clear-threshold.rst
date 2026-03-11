interfaces priority-flow-control global-clear-threshold
-------------------------------------------------------

**Minimum user role:** operator

When the VSQ size for a certain queue goes below the PFC clear threshold, then DN shall stop transmitting PFC pause frames on the interface. To configure the global PFC clear threshold on the interface that shall apply for each traffic class:

**Command syntax: global-clear-threshold [clear-threshold] [units]**

**Command mode:** config

**Hierarchies**

- interfaces priority-flow-control

**Note**

- Default clear-threshold is 2.5 Megabytes. An explicit configuration for a specific traffic class takes precedence over the inherited global configuration.

- Clear-threshold must be lower than the global pause-threshold or the traffic class specific pause-threshold

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter       | Description                                                                      | Range       | Default |
+=================+==================================================================================+=============+=========+
| clear-threshold | The PFC clear threshold for stopping transmission of pause frames for a certain  | 0-199999744 | 2500000 |
|                 | traffic class. The threshold is set for each traffic class separately.           |             |         |
+-----------------+----------------------------------------------------------------------------------+-------------+---------+
| units           |                                                                                  | | bytes     | bytes   |
|                 |                                                                                  | | kbytes    |         |
|                 |                                                                                  | | mbytes    |         |
+-----------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# priority-flow-control
    dnRouter(cfg-if-ge100-1/0/1-pfc)# global-clear-threshold 3 mbytes
    dnRouter(cfg-if-ge100-1/0/1-pfc)#


**Removing Configuration**

To revert to the default value
::

    dnRouter(cfg-if-ge100-1/0/13-pfc)# no global-clear-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
