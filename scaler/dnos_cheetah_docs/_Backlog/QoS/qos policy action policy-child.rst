qos policy action policy-child - N/A for this version 
------------------------------------------------------

**Command syntax: policy-child [policy-name]**

**Description:** configure a child policy.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule-default
	dnRouter(cfg-policy-myPolicy1-rule-default)# action
	dnRouter(cfg-myPolicy1-rule-default-action)# shape rate 20 percent 
	dnRouter(cfg-myPolicy1-rule-default-action)# policy-child myChildPolicy1
	
	dnRouter(cfg-myPolicy1-rule-default-action)# no policy-child
	
**Command mode:** config qos policy rule action

**TACACS role:** operator

**Note:**

no policy-child removes child policy configuration

**Help line:** set a child policy

**Parameter table:**

+-------------+--------+---------------+
| Parameter   | Values | Default value |
+=============+========+===============+
| Policy-name | String |               |
+-------------+--------+---------------+
