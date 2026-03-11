routing-policy qppb-policy rule action rate-limit
-------------------------------------------------

**Minimum user role:** operator

Sets a rate-limit for the traffic matched by the rule. 
Traffic exceeding the rate-limit will be dropped. 

To set the rate-limit:

**Command syntax: rate-limit [rate-limit] [units]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule action

**Note**

- You can define multiple set actions per rule.

- Rate limit is enforced per NPU core for all traffic received on the given core.

**Parameter table**

+------------+------------------------------------------------------+------------------+---------+
| Parameter  | Description                                          | Range            | Default |
+============+======================================================+==================+=========+
| rate-limit | The rate in kbits per second to limit the traffic to | 0, 64-1000000000 | \-      |
+------------+------------------------------------------------------+------------------+---------+
| units      |                                                      | | kbps           | kbps    |
|            |                                                      | | mbps           |         |
|            |                                                      | | gbps           |         |
+------------+------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# action
    dnRouter(cfg-qppb-policy-PL-1-rule-10-action) rate-limit 1000 kbps


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-action)# no rate-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
