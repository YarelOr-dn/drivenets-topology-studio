interfaces priority-flow-control pause-threshold max-threshold
--------------------------------------------------------------

**Minimum user role:** operator

The pause threshold is set dynamically between a minimum and maximum value, proportional to the amount of free buffer resources. The slope between the minimum and maximum values is determined by the alpha parameter. As the amount of free buffer resources increases, the pause threshold increases. When the VSQ size for a certain queue crosses the PFC pause threshold PFC pause frames are sent to the peer until it falls below the clear threshold.

**Command syntax: pause-threshold max-threshold [max-pause-threshold] [units1] min-threshold [min-pause-threshold] [units2] alpha [alpha]**

**Command mode:** config

**Hierarchies**

- interfaces priority-flow-control

**Note**

- The default pause-threshold is 200Kbytes, it is set by the global configuration. An explicit configuration for a specific interface or traffic class takes precedence over the inherited global configuration. To use dynamic PFC set the minimum threshold to be lower than the maximum threshold and add the alpha.

- The clear-threshold must be lower than the interface pause-threshold or the traffic class specific pause-threshold.

- The dynamic PFC formula (FADT):

- If a free resource/(2^alpha) is bigger than the max-threshold => threshold=max-threshold

- If a free resource/(2^alpha) is smaller than min-threshold (low resources) => threshold=min-threshold

- If the max-threshold > free-resource/(2^alpha) > min-threshold => threshold=free-resource/(2^alpha)

**Parameter table**

+---------------------+------------------------------------------------------------------------------+---------------+---------+
| Parameter           | Description                                                                  | Range         | Default |
+=====================+==============================================================================+===============+=========+
| max-pause-threshold | The PFC max pause threshold is the max VSQ size for triggering pause frames. | 256-200000000 | \-      |
+---------------------+------------------------------------------------------------------------------+---------------+---------+
| units1              |                                                                              | | bytes       | bytes   |
|                     |                                                                              | | kbytes      |         |
|                     |                                                                              | | mbytes      |         |
+---------------------+------------------------------------------------------------------------------+---------------+---------+
| min-pause-threshold | The PFC min pause threshold is the min VSQ size for triggering pause frames. | 256-200000000 | \-      |
+---------------------+------------------------------------------------------------------------------+---------------+---------+
| units2              |                                                                              | | bytes       | bytes   |
|                     |                                                                              | | kbytes      |         |
|                     |                                                                              | | mbytes      |         |
+---------------------+------------------------------------------------------------------------------+---------------+---------+
| alpha               | PFC alpha set dynamic threshold slope.                                       | 0-8           | \-      |
+---------------------+------------------------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# priority-flow-control
    dnRouter(cfg-if-ge100-1/0/1-pfc)# pause-threshold max-threshold 400 kbytes min-threshold 200 kbytes alpha 4
    dnRouter(cfg-if-ge100-1/0/1-pfc)# clear-threshold 100 kbytes


**Removing Configuration**

To revert to the default value
::

    dnRouter(cfg-if-ge100-1/0/13-pfc)# no pause-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
| 19.10   | Added Dynamic PFC  |
+---------+--------------------+
