routing-policy qppb-policy rule action qos-tag
----------------------------------------------

**Minimum user role:** operator

Has to be configured together with a drop-tag.
To configure the QoS tag that shall be set on the packets that match the rule:


**Command syntax: qos-tag [qos-tag]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule action

**Parameter table**

+-----------+------------------------+-------+---------+
| Parameter | Description            | Range | Default |
+===========+========================+=======+=========+
| qos-tag   | QoS-tag priority level | 0-7   | \-      |
+-----------+------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# action
    dnRouter(cfg-qppb-policy-PL-1-rule-10-action) qos-tag 5


**Removing Configuration**

To remove the qos-tag from the traffic-class-map:
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-action)# no qos-tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
