qos policy match traffic-class
------------------------------

**Command syntax: match traffic-class [traffic-class-map]**

**Description:** Configure match rule in a qos policy

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy MyQoSPolicy1 
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule 1 
	dnRouter(cfg-policy-MyQoSPOlicy1-rule-1)# match traffic-class myTrafficClassMap 
	
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# no match traffic-class
	
**Command mode:** config qos policy match rule

**TACACS role:** operator

**Note:** no 'match traffic-class' removes the configuration.

**Help line:** match a traffic-class-map

**Parameter table:**

+-------------------+--------+---------------+-------------------------------+
| Parameter         | Values | Default value | comment                       |
+===================+========+===============+===============================+
| traffic-class-map | String |               | Name of the traffic-class-map |
+-------------------+--------+---------------+-------------------------------+
