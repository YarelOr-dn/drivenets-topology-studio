interfaces priority-flow-control global-pause-threshold
-------------------------------------------------------

**Minimum user role:** operator

When the VSQ size for a certain queue crosses the PFC pause threshold, then PFC pause frames are sent to the peer until it falls bellow 50% of the PFC pause threshold. To configure the global PFC pause threshold on the interface that shall apply for each traffic class:

**Command syntax: global-pause-threshold [pause-threshold] [units]**

**Command mode:** config

**Hierarchies**

- interfaces priority-flow-control

**Note**

- Default pause-threshold is 5MB. An explicit configuration for a specific traffic class takes precedence over the inherited global configuration.

- Clear-threshold must be lower than the global pause-threshold or the traffic class specific pause-threshold

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------------+---------+
| Parameter       | Description                                                                      | Range         | Default |
+=================+==================================================================================+===============+=========+
| pause-threshold | The PFC pause threshold for triggering pause for a certain traffic class. The    | 256-200000000 | 5000000 |
|                 | threshold is set for each traffic class separately.                              |               |         |
+-----------------+----------------------------------------------------------------------------------+---------------+---------+
| units           |                                                                                  | | bytes       | bytes   |
|                 |                                                                                  | | kbytes      |         |
|                 |                                                                                  | | mbytes      |         |
+-----------------+----------------------------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# priority-flow-control
    dnRouter(cfg-if-ge100-1/0/1-pfc)# global-pause-threshold 5 mbytes
    dnRouter(cfg-if-ge100-1/0/1-pfc)#


**Removing Configuration**

To revert to the default value
::

    dnRouter(cfg-if-ge100-1/0/13-pfc)# no global-pause-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
