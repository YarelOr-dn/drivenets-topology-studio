qos
----

**Minimum user role:** operator

A Quality of Service (QoS) policy is a set of rules used for managing network bandwidth, delay, jitter, and packet loss. A rule comprises a traffic-class to match and a list of actions to perform if the traffic-class condition is met. Within a QoS policy, rules are defined in order of execution. Each rule has an ID and the rules are executed in ascending order. A default rule is implicitly created for each policy, such that traffic that does not match any of the defined rules will match the default rule.

The QoS policy is attached to interfaces. See "interfaces qos policy".

To enter the qos configuration hierarchy:

**Command syntax: qos**

**Command mode:** config


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos


.. **Removing Configuration**


.. **Help line:**

**Command History**

+-------------+-----------------------------------------+
|             |                                         |
| Release     | Modification                            |
+=============+=========================================+
|             |                                         |
| 6.0         | Command introduced for new hierarchy    |
+-------------+-----------------------------------------+
|             |                                         |
| 9.0         | QoS not supported                       |
+-------------+-----------------------------------------+
|             |                                         |
| 11.0        | Command reintroduced                    |
+-------------+-----------------------------------------+