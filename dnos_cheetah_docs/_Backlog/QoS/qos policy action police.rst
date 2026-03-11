qos policy action police - N/A for this version 
------------------------------------------------

**Command syntax: police committed-rate [committed-rate] [rate-units]** committed-burst [committed-burst] [burst-units] peak-burst [peak-burst] [burst-units] peak-rate [peak-rate] [rate-units] green-action [police-action] yellow-action [police-action] red-action [police-action]

**Description:** configure police for the matched traffic class.

The policer implements either srTCM or trTCM algorthms based on the configured parameters.

(see RFC2697 and RFC2698)

srTCM policer will be used when peak rate is not defined, and use the following parameters:

-  CIR (committed-rate)

-  CBS (committed-burst)

-  EBS (peak-burst). peak-burst must be equal or greater from cbs. If not explicitly configured, will be set to CBS.

trTCM policer will be used when peak rate is defined and use following parameters:

-  CIR (committed-rate)

-  CBS (committed-burst)

-  PBS (peak-burst). peak-burst must be equal or greater from cbs. If not explicitly configured, will be set to CBS.

-  PIR (peak-rate) peak-rate must be equal or greater than committed-rate.

Validation:

-  If peak-rate parameter (PIR) is not configured by user, policer-type is srTCM

-  When peak-rate parameter (PIR) is configured by user, policer-type is trTCM.

-  When Peak-burst not configured by user:

   -  If committed-burst (CBS) not configured by user, Peak-burst (EBS/PBS) is set to default value

   -  If committed-burst (CBS) configured by user, Peak-burst (EBS/PBS) is set to committed-burst (CBS) value

-  When Peak-burst configured by user, user configuration is the valid one.

-  Total bandwidth and max-bandwidth will not exceed 100% or its kbps units per each subinterface

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule 1
	dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
	dnRouter(cfg-policy-myPolicy1-rule-1)# action 
	dnRouter(cfg-myPolicy1-rule-1-action)# police committed-rate 50 percent committed-burst 4000 bytes 
	dnRouter(cfg-myPolicy1-rule-1-action)# police peak-rate 70 bytes 
	dnRouter(cfg-myPolicy1-rule-1-action)# police yellow-action set mpls exp topmost 4 
	
	dnRouter(cfg-myPolicy1-rule-1-action)# no police 
	dnRouter(cfg-myPolicy1-rule-1-action)# no police peak-rate
	
	
**Command mode:** config qos policy rule action

**TACACS role:** operator

**Note:**

no 'police' removes selected police configuration.

**Help line:** configure police

**Parameter table:**

+-------------------+------------------------------------------------+--------------------------------+
| Parameter         | Values                                         | Default value                  |
+===================+================================================+================================+
| Committed-rate    | If rate is percentage: <1-100>                 |                                |
|                   |                                                |                                |
|                   | Otherwise (rate is kbps): <1-100,000,000>      |                                |
+-------------------+------------------------------------------------+--------------------------------+
| Rate-units value  | Percent \| kbps                                |                                |
+-------------------+------------------------------------------------+--------------------------------+
| Committed-burst   | <1-1,000> for msec                             | 100 msec                       |
|                   |                                                |                                |
|                   | <1-12,500,000,000> for bytes                   |                                |
+-------------------+------------------------------------------------+--------------------------------+
| Burst-units       | msec \| bytes                                  |                                |
+-------------------+------------------------------------------------+--------------------------------+
| Police action     | set [police-set-action] \| forward \| drop     | Default green-action: forward  |
|                   |                                                |                                |
|                   |                                                | Default yellow-action: forward |
|                   |                                                |                                |
|                   |                                                | Default red-action: drop       |
+-------------------+------------------------------------------------+--------------------------------+
| police-set-action | mpls exp imposition <0-7> \|                   |                                |
|                   |                                                |                                |
|                   | mpls exp topmost <0-7>                         |                                |
|                   |                                                |                                |
|                   | precedence <0-7> \|                            |                                |
|                   |                                                |                                |
|                   | dscp <0-63> \|                                 |                                |
|                   |                                                |                                |
|                   | 802.1p <0-7>                                   |                                |
|                   |                                                |                                |
|                   | qos-tag <0-7>                                  |                                |
|                   |                                                |                                |
|                   | red-tag <1-3>                                  |                                |
+-------------------+------------------------------------------------+--------------------------------+
| Peak-rate         | If rate is percentage: <0-100>                 |                                |
|                   |                                                |                                |
|                   | Otherwise (rate is kbps): <0-100,000,000>      |                                |
+-------------------+------------------------------------------------+--------------------------------+
| Peak-burst        | <1-1,000> for msec                             | 100 msec                       |
|                   |                                                |                                |
|                   | <1-12,500,000,000> for bytes                   |                                |
|                   |                                                |                                |
|                   | not less than committed-burst                  |                                |
+-------------------+------------------------------------------------+--------------------------------+
