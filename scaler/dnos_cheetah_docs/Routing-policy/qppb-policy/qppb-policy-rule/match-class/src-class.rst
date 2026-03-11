routing-policy qppb-policy rule match-class src-class
-----------------------------------------------------

**Minimum user role:** operator

To Configure a soucre class as part of the match criteria of the rule.

**Command syntax: src-class [src-class]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule match-class

**Parameter table**

+-----------+---------------------+-------+---------+
| Parameter | Description         | Range | Default |
+===========+=====================+=======+=========+
| src-class | The Source Class Id | \-    | any     |
+-----------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# match-class
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class) src-class 100
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)


**Removing Configuration**

To remove the src-class from the match-class
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)# no src-class

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
