routing-policy qppb-policy rule description
-------------------------------------------

**Minimum user role:** operator

To add a meaningful description for a qppb-policy-rule:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule

**Parameter table**

+-------------+---------------------------------------+------------------+---------+
| Parameter   | Description                           | Range            | Default |
+=============+=======================================+==================+=========+
| description | holds a user description for the rule | | string         | \-      |
|             |                                       | | length 1-255   |         |
+-------------+---------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# description "rule that matches Customer-A traffic"
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)#


**Removing Configuration**

To remove the description from the rule
::

    dnRouter(dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
