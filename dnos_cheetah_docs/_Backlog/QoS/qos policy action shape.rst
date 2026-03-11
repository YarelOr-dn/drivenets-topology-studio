qos policy action shape - N/A for this version 
-----------------------------------------------

**Command syntax: shape rate [shape_rate_value] [shape_rate_units]** [burst-value] [burst-units]

**Description:** configure a shaper

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule-default
	dnRouter(cfg-policy-myPolicy1-rule-default)# action
	dnRouter(cfg-myPolicy1-rule-default-action)# shape rate 20 percent 
	
	dnRouter(cfg-myPolicy1-rule-default-action)# no shape rate
	
**Command mode:** config qos policy rule-default action

**TACACS role:** operator

**Note:**

no shape removes shape configuration

**Help line:** configure a shaper

**Parameter table:**

+------------------+------------------------------+---------------+
| Parameter        | Values                       | Default value |
+==================+==============================+===============+
| Shape_rate_value | Percentage units: <1-100>    |               |
|                  |                              |               |
|                  | Kbps : <1, 100, 000, 000>    |               |
+------------------+------------------------------+---------------+
| Burst-value      | <1-1,000> for msec           | 100 msec      |
|                  |                              |               |
|                  | <1-12,500,000,000> for bytes |               |
+------------------+------------------------------+---------------+
| Burst-units      | Bytes/msec                   |               |
+------------------+------------------------------+---------------+
