qos policy rule 
----------------

**Command syntax: rule [rule-id]**

**Description:** Configure rule in a qos policy

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy MyQoSPolicy1 
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule 1 
	
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# no rule 1 
	
**Command mode:** config qos policy

**TACACS role:** operator

**Note:**

no command removes the rule configuration.

Rule id determines the order in the policy. The rules are arranged in ascending order. (lower id has higher priority in the policy)

**Help line:** rule identifier

**Parameter table:**

+-----------+---------+---------------+---------+
| Parameter | Values  | Default value | comment |
+===========+=========+===============+=========+
| Rule-id   | 1-65535 |               |         |
+-----------+---------+---------------+---------+
