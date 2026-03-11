qos policy rule description 
----------------------------

**Command syntax: description [description-text]**

**Description:** Configure a rule description

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy MyQoSPolicy1 
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule 1 
	dnRouter(cfg-policy-MyQoSPOlicy1-rule-1)# description real time service 
	
	dnRouter(cfg-policy-MyQoSPOlicy1-rule-1)# no description
	
**Command mode:** config qos policy rule

**TACACS role:** operator

**Note:** 'no description' deletes the configuration

**Help line:** text description of the rule

**Parameter table:**

+------------------+--------+---------------+---------------------------------------------------+
| Parameter        | Values | Default value | Description/comment                               |
+==================+========+===============+===================================================+
| Description-text | String |               | Up to 64 characters enclosed with quotation marks |
+------------------+--------+---------------+---------------------------------------------------+
