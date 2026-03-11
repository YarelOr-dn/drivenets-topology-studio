qos policy rule action set drop-tag
-----------------------------------

**Minimum user role:** operator

Actions set a new value for specific parameters. If a set drop-tag is not configured, a drop priority green is assigned.

To create a set action:

**Command syntax: drop-tag [drop-tag]**

**Command mode:** config

**Hierarchies**

- qos policy rule action set

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+-----------+---------------------+------------+---------+
| Parameter | Description         | Range      | Default |
+===========+=====================+============+=========+
| drop-tag  | Drop priority color | | green    | \-      |
|           |                     | | yellow   |         |
+-----------+---------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# set
    dnRouter(cfg-myPolicy1-rule-1-action-set)# drop-tag yellow


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-set)# no drop-tag

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
