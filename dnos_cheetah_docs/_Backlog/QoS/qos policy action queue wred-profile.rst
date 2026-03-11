qos policy action queue wred-profile
------------------------------------

**Command syntax: queue [forwarding-class] wred-profile [wred-profile]**

**Description:** set a queue for the matched traffic class.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule 1
	dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
	dnRouter(cfg-policy-myPolicy1-rule-1)# action 
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af wred-profile my_profile 
	
	dnRouter(cfg-policy-myPolicy1-rule-1)# no action af wred-profile 
	
**Command mode:** config

**TACACS role:** operator

**Note:** In order to preserve hardware utilization, it is recommended to configure same 4 wred-profiles to set of 4 af queues.

Validation:

Maximum wred curve value cannot be higher than queue size.

**Help line:** configure qos policy rule action wred-profile on queue

**Parameter table:**

+------------------+--------+---------------+-------------------------------------+
| Parameter        | Values | Default value | comments                            |
+==================+========+===============+=====================================+
| forwarding-class | af     |               |                                     |
+------------------+--------+---------------+-------------------------------------+
| wred-profile     | string |               | Taken from configured wred profiles |
+------------------+--------+---------------+-------------------------------------+
