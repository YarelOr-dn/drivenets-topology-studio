routing-policy qppb-policy rule actions qos-tag
-----------------------------------------------

**Minimum user role:** operator

To Configure QoS tag that shall be set on the packets that match the rule.

**Command syntax: qos-tag [qos-tag]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule actions

**Parameter table**

+-----------+------------------------+-------+---------+
| Parameter | Description            | Range | Default |
+===========+========================+=======+=========+
| qos-tag   | QoS-tag priority level | 0..7  | \-      |
+-----------+------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# actions
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions) qos-tag 5
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)


**Removing Configuration**

To remove the qos-tag from the traffic-class-map
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)# no qos-tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17      | Command introduced |
+---------+--------------------+
