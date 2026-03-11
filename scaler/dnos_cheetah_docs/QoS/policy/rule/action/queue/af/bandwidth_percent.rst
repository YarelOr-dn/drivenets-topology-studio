qos policy rule action queue forwarding-class af bandwidth percent
------------------------------------------------------------------

**Minimum user role:** operator

Queue actions create a queue through which to send traffic that meet the rule's matching criteria. For additional information on queues, see "Forwarding Classes and Queues". This command creates a queue for the specified traffic-class with specific bandwidth values. For priority queues (ef, hp, and sef), the "max-bandwidth" parameter is configured to prevent starvation of the lower priority queues. For af and df queues, the "bandwidth" parameter determines the ratio of the shared bandwidth that each queue can use.

For the af and df queues, if the total bandwidth does not equal 100%, the remaining bandwidth that is not configured, is distributed among the queues according to their relative weight.

For example if the bandwidth allocations of the af and df queues are set to 5%, 10%, 20%, and 40% (total of 75%), the remaining 25% of the bandwidth will be shared in proportion among the queues, as if the queues were configured with 6.66%, 13.33%, 26.66%, 53.33% bandwidth settings.

To create a queue per traffic-class:

**Command syntax: bandwidth [bandwidth-percent] percent**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue forwarding-class af

**Note**

- max-bandwidth is applicable to sef, hp, and ef forwarding classes only. When the maximum rate is crossed, packets will be dropped to avoid starvation of the lower priority queues.

- bandwidth is applicable to the af and df forwarding classes only. The queue action for the df forwarding-class is available for the default rule only.

- The burst-value is configured implicitly by the system when configuring "max-bandwidth" with a value of 20% of max-bandwidth.

- Up to 6 af forwarding-class queues can be used, with a total of 8 queues.

- Only one queue action for super-ef forwarding-class is allowed per policy.

- Only one queue action for ef forwarding-class is allowed per policy.

- Only one queue action for hp forwarding-class is allowed per policy.

- Queue action for df forwarding-class is available in rule default only.

**Parameter table**

+-------------------+---------------------------------+-------+---------+
| Parameter         | Description                     | Range | Default |
+===================+=================================+=======+=========+
| bandwidth-percent | scheduler WRR weight in precent | 1-100 | \-      |
+-------------------+---------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# queue forwarding-class
    dnRouter(cfg-myPolicy1-rule-1-action-queue)# af
    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# bandwidth 20 percent


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# no bandwidth

**Command History**

+---------+-------------------------------------------------------+
| Release | Modification                                          |
+=========+=======================================================+
| 11.2    | Command introduced                                    |
+---------+-------------------------------------------------------+
| 15.1    | Added support for hp (high-priority) forwarding class |
+---------+-------------------------------------------------------+
