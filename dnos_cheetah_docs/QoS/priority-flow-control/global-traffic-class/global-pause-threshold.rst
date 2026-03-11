qos priority-flow-control global-traffic-class global-pause-threshold max-threshold
-----------------------------------------------------------------------------------

**Minimum user role:** operator

The global pause threshold is set dynamically between a minimum and maximum value, proportional to the amount of free buffer resources. The slope between the minimum and maximum values is determined by the alpha parameter. As the amount of free buffer resources increases, the pause threshold increases. When the size of a VSQ exceeds the PFC pause threshold, PFC pause frames are sent to the peer until the queue size falls below the clear threshold. Lower hierarchies use global thresholds unless they have their own specific configuration. to configure the global pause threshold:

**Command syntax: global-pause-threshold max-threshold [global-max-pause-threshold] [units1] min-threshold [global-min-pause-threshold] [units2] alpha [global-alpha]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control global-traffic-class

**Note**

- The default minimum and maximum global-pause-threshold is 200KB. An explicit configuration for a specific traffic class takes precedence over the inherited global configuration. To use dynamic PFC set the global-min-pause-threshold to be lower than the global-max-pause-threshold and add the global-alpha.

- The clear-threshold must be lower than the global pause-threshold or the traffic class specific pause-threshold.

- The dynamic PFC formula (FADT): 

- If a free resource/(2^alpha) is bigger than the max-threshold => threshold=max-threshold

- If a free resource/(2^alpha) is smaller than min-threshold (low resources) => threshold=min-threshold

- If the max-threshold > free-resource/(2^alpha) > min-threshold => threshold=free-resource/(2^alpha)

**Parameter table**

+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| Parameter                  | Description                                                                      | Range         | Default |
+============================+==================================================================================+===============+=========+
| global-max-pause-threshold | The PFC max pause threshold is the max VSQ size to start triggering pause frames | 256-200000000 | \-      |
|                            | per traffic-class.                                                               |               |         |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| units1                     |                                                                                  | | bytes       | bytes   |
|                            |                                                                                  | | kbytes      |         |
|                            |                                                                                  | | mbytes      |         |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| global-min-pause-threshold | The PFC min pause threshold is the min VSQ size to start triggering pause frames | 256-200000000 | \-      |
|                            | per traffic-class.                                                               |               |         |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| units2                     |                                                                                  | | bytes       | bytes   |
|                            |                                                                                  | | kbytes      |         |
|                            |                                                                                  | | mbytes      |         |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| global-alpha               | PFC alpha sets the dynamic threshold slope for a specific traffic class.         | 0-8           | \-      |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# traffic-class 3
    dnRouter(cfg-qos-pfc-tc3)# global-pause-threshold max-threshold 300 kbytes min-threshold 150 kbytes global-alpha 4
    dnRouter(cfg-qos-pfc-tc3)#


**Removing Configuration**

To revert to the default value
::

    dnRouter(cfg-qos-pfc)# no pause-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
