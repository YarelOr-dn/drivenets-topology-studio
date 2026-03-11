routing-policy qppb-policy rule actions rate-limit kbps
-------------------------------------------------------

**Minimum user role:** operator

Set a rate-limit for the traffic matched by the rule. Traffic exceeding the rate-limit will be dropped.

To create a set action:

**Command syntax: rate-limit [rate-limit] kbps**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule actions

**Note**

- You can define multiple set actions per rule.

- Rate limit in enforce per NPU core for all traffic received on the given core.

**Parameter table**

+------------+----------------------------------------------------+------------------+---------+
| Parameter  | Description                                        | Range            | Default |
+------------+----------------------------------------------------+------------------+---------+
| rate-limit | The rate in kbits per second to limit the traffic  | 0, 64-1000000000 | \-      |
+------------+----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# actions
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions) rate-limit 1000 kbps


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)# no rate-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
