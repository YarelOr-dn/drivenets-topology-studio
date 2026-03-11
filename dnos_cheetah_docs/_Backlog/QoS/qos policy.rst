qos policy 
-----------

**Command syntax: qos policy [policy_name]**

**Description:** configure qos policy

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy MyQoSPolicy1 
	
	dnRouter(cfg-qos)# no policy MyQoSPolicy1 
	
	
**Command mode:** config

**TACACS role:** operator

**Note:**

no command remove the policy configuration

validation: a policy can't be deleted if it is attached to an interface. The following warning will be printed:

"Error: cannot delete qos policy <qos policy name>. qos policy is attached to interface."

**Help line:** Configure qos policy

**Parameter table:**

+-------------+--------+---------------+
| Parameter   | Values | Default value |
+=============+========+===============+
| Policy-name | String |               |
+-------------+--------+---------------+
