qos policy rule action shape average-rate percent
-------------------------------------------------

**Minimum user role:** operator

Shape the output of an interface or sub-interface to the specified rate. The shape action should be applied on rule default, in a hierarchical policy, and may be used in combination with child-policy action to control queuing and remarking on egress.

**Command syntax: average-rate [average-rate-percent] percent**

**Command mode:** config

**Hierarchies**

- qos policy rule action shape

**Parameter table**

+----------------------+------------------------+-------+---------+
| Parameter            | Description            | Range | Default |
+======================+========================+=======+=========+
| average-rate-percent | shaper rate in percent | 0-100 | \-      |
+----------------------+------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1
    dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule default
    dnRouter(cfg-policy-MyQoSPOlicy1-rule-default)# action
    dnRouter(cfg-MyQSPOlicy1-rule-default-action)# shape
    dnRouter(cfg-rule-default-action-shape)# average-rate 10 percent


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-rule-default-action-shape)# no average-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
