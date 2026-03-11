qos policy action queue bandwidth 
----------------------------------

**Command syntax: queue [forwarding-class]** [cmd-type] **[bandwidth value] [bandwidth units]**

**Description:** set a queue for the matched traffic class.

Creates a queue for the traffic-class with the specified forwarding-class properties.

The properties that are determined by the forwarding class are scheduling priority , queue size and wred profile parameters of the queue. (see wred-profile , queue size) .

*bandwidth* is allowed only on af queues, and it set the relative rate allocated for this queue

*Max-bandwidth* is allowed only on ef and super-ef queues. Max-bandwidth defines the max rate of traffic from these queue. The configuration is intended to avoid starvation of lower priority forwarding classes (assured-forwarding queues)

[STRIKEOUT:Best-effort has no guaranteed bandwidth, it will be served only if higher forwarding classes are silent.]

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule 1
	dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
	dnRouter(cfg-policy-myPolicy1-rule-1)# action 
	dnRouter(cfg-myPolicy1-rule-1-action)# queue af bandwidth 20 percent 
	
	
	dnRouter(cfg-policy-myPolicy1-rule-1)# no action queue af bandwidth 
	
	
	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule 1
	dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
	dnRouter(cfg-policy-myPolicy1-rule-1)# action 
	dnRouter(cfg-myPolicy1-rule-1-action)# queue super-ef max-bandwidth 20 percent
	dnRouter(cfg-myPolicy1-rule-1-action)# queue super-ef max-bandwidth 1000 kbps
	dnRouter(cfg-myPolicy1-rule-1-action)# queue super-ef max-bandwidth 1000 mbps
	dnRouter(cfg-myPolicy1-rule-1-action)# queue super-ef max-bandwidth 10 gbps
	
	dnRouter(cfg-myPolicy1-rule-1-action)# no queue super-ef max-bandwidth
	 
	
**Command mode:** config qos policy rule action

**TACACS role:** operator

**Note:**

Only one queue action in super-ef forwarding-class is allowed per policy

Only one queue action in ef forwarding-class is allowed per policy

MAX_PORT_RATE is the physical port rate (e.g ge400-0/0/0 has rate of 400 gbps)

Validation:

-  Total bandwidth and max-bandwidth will not exceed 100% or its kbps units per each interface

-  On bundle interfaces, only percent configuration allowed

-  Burst-value configured implicitly by system when configuring max-bandwidth with value of 20% of max-bandwidth.

**Help line:** set a queue

**Parameter table:**

+------------------+-----------------------------------+---------------+---------------------------------------------------------------------------------+
| Parameter        | Values                            | Default value | comments                                                                        |
+==================+===================================+===============+=================================================================================+
| forwarding-class | Super-ef / ef / af                |               |                                                                                 |
+------------------+-----------------------------------+---------------+---------------------------------------------------------------------------------+
| cmd-type         | Max-bandwidth / Bandwidth         |               | Max-bandwidth is allowed only on *ef* and *super-ef* queues.                    |
|                  |                                   |               |                                                                                 |
|                  |                                   |               | Bandwidth is allowed only on *af* queues.                                       |
+------------------+-----------------------------------+---------------+---------------------------------------------------------------------------------+
| Bandwidth-value  | For percent units : <1-100>       |               | Bandwidth value is mandatory for bandwidth and max-bandwidth commands           |
|                  |                                   |               |                                                                                 |
|                  | For bps units: <1-MAX_PORT_RATE > |               |                                                                                 |
+------------------+-----------------------------------+---------------+---------------------------------------------------------------------------------+
| Bandwidth-units  | percent                           |               | Bandwidth-units is mandatory parameter for bandwidth and max-bandwidth commands |
|                  |                                   |               |                                                                                 |
|                  | kbps                              |               | Note:                                                                           |
|                  |                                   |               |                                                                                 |
|                  | mbps                              |               | Bandwidth units must be percent.                                                |
|                  |                                   |               |                                                                                 |
|                  | gbps                              |               |                                                                                 |
+------------------+-----------------------------------+---------------+---------------------------------------------------------------------------------+
