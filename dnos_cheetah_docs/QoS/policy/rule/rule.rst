qos policy rule
---------------

**Minimum user role:** operator

You can create multiple rules per policy and one default rule. After you create a rule, you enter the rule configuration mode indicated by the prompt for either the rule id or the default rule) and you can proceed to add a description and configure actions for the specific rule. See "qos policy rule description" and "qos policy rule action".

To create a rule, make sure that you are in QoS policy configuration mode:

**Command syntax: rule [rule]**

**Command mode:** config

**Hierarchies**

- qos policy

**Parameter table**

+-----------+------------------------------------------+-------+---------+
| Parameter | Description                              | Range | Default |
+===========+==========================================+=======+=========+
| rule      | References the configured id of the rule | \-    | \-      |
+-----------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1
    dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule 1


**Removing Configuration**

To delete the rule:
::

    dnRouter(cfg-qos-policy-MyQoSPOlicy1)# no rule 1

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
| 15.0    | Updated rule-id range                                           |
+---------+-----------------------------------------------------------------+
