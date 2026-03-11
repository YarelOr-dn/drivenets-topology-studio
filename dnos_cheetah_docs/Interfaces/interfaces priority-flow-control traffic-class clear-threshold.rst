interfaces priority-flow-control traffic-class clear-threshold
--------------------------------------------------------------

**Minimum user role:** operator

When the VSQ size for a certain queue goes below the PFC clear threshold, the transmition of PFC pause frames on the interface is stopped. To configure the PFC clear threshold on the interface for a specific traffic class:

**Command syntax: clear-threshold [clear-threshold] [units]**

**Command mode:** config

**Hierarchies**

- interfaces priority-flow-control traffic-class

**Note**

- Default clear-threshold is 80Kbytes, it is set by global configuration. An explicit configuration under a certain traffic class takes precendence over the inherited global configuration

- Clear-threshold must be lower than the interface pause-threshold or the traffic class specific pause-threshold

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter       | Description                                                                      | Range       | Default |
+=================+==================================================================================+=============+=========+
| clear-threshold | The PFC clear threshold for stopping transmission of pause frames for a certain  | 0-199999744 | \-      |
|                 | traffic class. The threshold is configured for each traffic class separately.    |             |         |
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
    dnRouter(cfg-if-ge100-1/0/1-pfc)# traffic-class 2
    dnRouter(cfg-ge100-1/0/1-pfc-tc2)# clear-threshold 100 kbytes


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-ge100-1/0/13-pfc-tc2)# no clear-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
