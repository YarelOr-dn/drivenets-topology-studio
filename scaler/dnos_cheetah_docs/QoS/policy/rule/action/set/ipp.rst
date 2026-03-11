qos policy rule action set ipp
------------------------------

**Minimum user role:** operator

To set the IP Precedence value on egress according to the qos-tag and color.

**Command syntax: ipp [qos-tag] [drop-tag] [precedence]**

**Command mode:** config

**Hierarchies**

- qos policy rule action set

**Note**

- This action is identical to set dscp action.

- You can define multiple set actions per rule.

**Parameter table**

+------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter  | Description                                                                      | Range      | Default |
+============+==================================================================================+============+=========+
| qos-tag    | qos-tag identifier or all. usefull when more than one qos-tag is mapped to the   | \-         | \-      |
|            | rule.                                                                            |            |         |
+------------+----------------------------------------------------------------------------------+------------+---------+
| drop-tag   | drop-tag identifier or all. usefull when more than one color is mapped to the    | | green    | \-      |
|            | rule.                                                                            | | yellow   |         |
|            |                                                                                  | | all      |         |
+------------+----------------------------------------------------------------------------------+------------+---------+
| precedence | the ip precedence remark value.                                                  | 0-7        | \-      |
+------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# set
    dnRouter(cfg-myPolicy1-rule-1-action-set)# ipp 6 green 0


**Removing Configuration**

To remove a set action:
::

    dnRouter(cfg-myPolicy1-rule-1-action-set)# no ipp 6 green

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
