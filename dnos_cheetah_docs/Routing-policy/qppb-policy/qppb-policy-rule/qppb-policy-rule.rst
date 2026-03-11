routing-policy qppb-policy rule
-------------------------------

**Minimum user role:** operator

You can create multiple rules per policy. After you create a rule, you enter the rule configuration mode (indicated by the prompt for the rule id) and
you can proceed to add a description and configure actions for the specific rule. See "qppb policy rule description" and "qppb policy rule action".

To create a rule, make sure that you are in QoS policy configuration mode:

**Command syntax: rule [qppb-policy-rule]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy

**Parameter table**

+------------------+---------------------------------------+---------+---------+
| Parameter        | Description                           | Range   | Default |
+==================+=======================================+=========+=========+
| qppb-policy-rule | the unique rule id inside the policy. | 1-65535 | \-      |
+------------------+---------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)#


**Removing Configuration**

To delete the qppb rule:
::

    dnRouter(cfg-rpl-qppb-policy-PL-1)# no rule 10 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
