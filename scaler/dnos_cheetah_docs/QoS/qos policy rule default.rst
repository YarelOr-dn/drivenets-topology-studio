qos policy rule default
-----------------------

**Minimum user role:** operator

A single default rule is automatically created for each policy. This is the rule that is applied when no other rule matches the traffic, so it can only be configured with actions, and not with match criteria. The default rule has the lowest rule priority.

On an ingress policy, rule default sets the qos-tag to 0 and drop-tag to green by default.

On an egress policy, rule default uses the df (Default Forwarding) queue by default.

To configure the default rule for the policy:


**Command syntax: rule default**

**Command mode:** config

**Hierarchies**

- qos policy

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy MyQoSPolicy1
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule default
	dnRouter(cfg-policy-MyQoSPOlicy1-rule-default)#


**Removing Configuration**

To revert the default rule to its default value:
::

	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# no rule default


.. **Help line:** rule default


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+