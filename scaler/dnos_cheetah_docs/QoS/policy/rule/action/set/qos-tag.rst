qos policy rule action set qos-tag
----------------------------------

**Minimum user role:** operator

To classify traffic to a Per Hop Behavior (PHB). The qos-tag 0 is assigned by default if set qos-tag action is not configured.

**Command syntax: qos-tag [qos-tag]**

**Command mode:** config

**Hierarchies**

- qos policy rule action set

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+-----------+------------------------+-------+---------+
| Parameter | Description            | Range | Default |
+===========+========================+=======+=========+
| qos-tag   | QoS-tag priority level | 0-7   | \-      |
+-----------+------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# set
    dnRouter(cfg-myPolicy1-rule-1-action-set)# qos-tag 5


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-set)# no qos-tag

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 5.1.0   | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 6.0     | When moving into different modes, higher mode names are removed |
+---------+-----------------------------------------------------------------+
| 9.0     | QoS not supported                                               |
+---------+-----------------------------------------------------------------+
| 11.2    | Command re-introduced                                           |
+---------+-----------------------------------------------------------------+
| 16.1    | Split from the generic QoS Policy Action Set command            |
+---------+-----------------------------------------------------------------+
