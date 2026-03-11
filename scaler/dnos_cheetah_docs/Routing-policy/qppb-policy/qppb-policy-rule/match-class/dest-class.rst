routing-policy qppb-policy rule match-class dest-class
------------------------------------------------------

**Minimum user role:** operator

To Configure a destination class as part of the match criteria of the rule.

**Command syntax: dest-class [dest-class]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule match-class

**Parameter table**

+------------+--------------------------+-------+---------+
| Parameter  | Description              | Range | Default |
+============+==========================+=======+=========+
| dest-class | The Destination Class Id | \-    | any     |
+------------+--------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# match-class
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class) dest-class 65
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)


**Removing Configuration**

To remove the dest-class from the match-class
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)# no dest-class

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
