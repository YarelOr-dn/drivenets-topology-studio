routing-policy policy rule set qppb-src-class
---------------------------------------------

**Minimum user role:** operator

To set the Source Class value for routes that match the match-criteria.

**Command syntax: set qppb-src-class [qppb-src-class]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+----------------+--------------------------+-------+---------+
| Parameter      | Description              | Range | Default |
+================+==========================+=======+=========+
| qppb-src-class | The QPPB Source Class Id | 1-128 | \-      |
+----------------+--------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# set qppb-src-class 25

    dnRouter(cfg-rpl-policy-rule-20)# match community COMMUNITY_LIST_1
    dnRouter(cfg-rpl-policy-rule-10)# set qppb-src-class 30


**Removing Configuration**

To remove set action:
::

    dnRouter(cfg-rpl-policy-rule-10)# no set qppb-src-class

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
