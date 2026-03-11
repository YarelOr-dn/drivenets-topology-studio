routing-policy qppb-policy rule action
--------------------------------------

**Minimum user role:** operator

To configure the actions that should be applied when the rule is matched:


**Command syntax: action**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# action
    dnRouter(cfg-qppb-policy-PL-1-rule-10-action)


**Removing Configuration**

To remove the actions from the rule:
::

    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# no action

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
