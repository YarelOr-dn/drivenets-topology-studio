routing-policy qppb-policy rule match-class
-------------------------------------------

**Minimum user role:** operator

To Configure the match criteria for the rule.

**Command syntax: match-class**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# match-class
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)


**Removing Configuration**

To restore the match-class parameters to their defaults
::

    dnRouter(cdnRouter(cfg-rpl-qppb-policy-PL-1-rule-10))# no match-class

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
