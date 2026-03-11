qos policy rule action set mpls-exp
-----------------------------------

**Minimum user role:** operator

To configure a set action for the matched traffic class.

**Command syntax: mpls-exp [mpls-exp]**

**Command mode:** config

**Hierarchies**

- qos policy rule action set

**Note**

- The mpls-exp action modifies the EXP bits of an incoming topmost swapped MPLS header. The action can only be set if mpls-swap-exp-edit-mode parameter is set to copy. The MPLS EXP bits are set on the outgoing swapped MPLS header, as well as any additional pushed MPLS headers added at egress.

- You can define multiple set actions per rule.

**Parameter table**

+-----------+----------------------------------+-------+---------+
| Parameter | Description                      | Range | Default |
+===========+==================================+=======+=========+
| mpls-exp  | MPLS topmost EXP bits (TC field) | 0-7   | \-      |
+-----------+----------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# set
    dnRouter(cfg-myPolicy1-rule-1-action-set)# mpls-exp 3


**Removing Configuration**

To remove a set action:
::

    dnRouter(cfg-myPolicy1-rule-1-action-set)# no mpls-exp

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
| 15.0    | Added support for set mpls-exp                                  |
+---------+-----------------------------------------------------------------+
| 16.1    | Split from the generic QoS Policy Action Set command            |
+---------+-----------------------------------------------------------------+
