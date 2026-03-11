qos policy action queue size
----------------------------

**Command syntax: queue [forwarding-class] size [queue-size]** [knob]

**Description:** set a queue size as forwarding-class property.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule 1
	dnRouter(cfg-policy-myPolicy1-rule-1)# action 
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af size 100
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af size 100 milliseconds
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af size 1500 microseconds
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af size 100 packets
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af size 1024 bytes
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af size 1024 kilobytes
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af size 1024 megabytes
	
	
	
	dnRouter(cfg-policy-myPolicy1-rule-1)# no action queue af size 
	dnRouter(cfg-myPolicy1-rule-1-action)# no queue af size
	
	
	
**Command mode:** config

**TACACS role:** operator

**Note:**

-  When configuring size, assumption packet size is 256 Bytes

Validation:

-  Single queue size will not pass maximal HBM size (33.6Gb), validation includes sum of members in bundle interface

-  Bundle interfaces shall be attached only with time knob queue size

**Help line:** set a queue size

**Parameter table:**

+------------------+----------------------------------------+---------------------------------+
| Parameter        | Values                                 | Default value                   |
+==================+========================================+=================================+
| forwarding-class | Super-ef / ef / af                     |                                 |
+------------------+----------------------------------------+---------------------------------+
| queue-size       | For time units : <1-2000> milliseconds | 10 milliseconds for ef/super-ef |
|                  |                                        |                                 |
|                  | For packet units: <1-32M >             | 50 milliseconds for af          |
|                  |                                        |                                 |
|                  | For bytes units: <256B-8GB >           |                                 |
+------------------+----------------------------------------+---------------------------------+
| knob             | milliseconds                           | milliseconds                    |
|                  |                                        |                                 |
|                  | microseconds                           |                                 |
|                  |                                        |                                 |
|                  | packets                                |                                 |
|                  |                                        |                                 |
|                  | bytes                                  |                                 |
|                  |                                        |                                 |
|                  | kilobytes                              |                                 |
|                  |                                        |                                 |
|                  | megabytes                              |                                 |
+------------------+----------------------------------------+---------------------------------+
