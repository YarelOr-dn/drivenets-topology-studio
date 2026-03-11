qos policy rule action set pcp-dei
----------------------------------

**Minimum user role:** operator

To set pcp-dei 4 bits in 802.1Q header according to qos-tag and color. The qos-tag is either one of the qos-tag 0..7 assigned to the rule or 'all', to apply to all qos-tags assigned to the rule.

The drop-tag is either green or yellow or all to indicate both.

**Command syntax: pcp-dei [qos-tag] [drop-tag] [pcp-dei]**

**Command mode:** config

**Hierarchies**

- qos policy rule action set

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                      | Range      | Default |
+===========+==================================================================================+============+=========+
| qos-tag   | qos-tag identifier or all. usefull when more than one qos-tag is mapped to the   | \-         | \-      |
|           | rule.                                                                            |            |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+
| drop-tag  | drop-tag identifier or all. usefull when more than one color is mapped to the    | | green    | \-      |
|           | rule.                                                                            | | yellow   |         |
|           |                                                                                  | | all      |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+
| pcp-dei   | the pcp-dei marking value.                                                       | 0-15       | \-      |
+-----------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# set
    dnRouter(cfg-myPolicy1-rule-1-action-set)# pcp-dei all all 15


**Removing Configuration**

To remove a set action:
::

    dnRouter(cfg-myPolicy1-rule-1-action-set)# no pcp-dei

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
| 15.1    | Added support for pcp-dei (drop eligible indicator)             |
+---------+-----------------------------------------------------------------+
| 16.1    | Split from the generic QoS Policy Action Set command            |
+---------+-----------------------------------------------------------------+
