routing-policy policy rule set qppb-dest-class
----------------------------------------------

**Minimum user role:** operator

To set the Destination Class value for routes that match the match-criteria.

**Command syntax: set qppb-dest-class [qppb-dest-class]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+-----------------+-------------------------------+-------+---------+
| Parameter       | Description                   | Range | Default |
+=================+===============================+=======+=========+
| qppb-dest-class | The QPPB Destination Class Id | 1-128 | \-      |
+-----------------+-------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# set qppb-dest-class 25

    dnRouter(cfg-rpl-policy-rule-20)# match community COMMUNITY_LIST_1
    dnRouter(cfg-rpl-policy-rule-10)# set qppb-dest-class 30


**Removing Configuration**

To remove set action:
::

    dnRouter(cfg-rpl-policy-rule-10)# no set qppb-dest-class

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
