qos policy action set 
----------------------

**Command syntax: set [set-action]**

**Description:** configure a set action for the matched traffic class.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule 1
	dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
	dnRouter(cfg-policy-myPolicy1-rule-1)# action 
	dnRouter(cfg-myPolicy1-rule-1-action)# set dscp 5
	
	dnRouter(cfg-policy-myPolicy1-rule-1)# no action 
	dnRouter(cfg-myPolicy1-rule-1-action)# no set dscp
	
**Command mode:** config qos policy rule action

**TACACS role:** operator

**Note:**

no 'action' removes whole selected action set

no 'set' removes internal leaf.

Set on 802.1p parameter relates only on sub-interfaces attached policies

**Help line:** configure a set action

**Parameter table:**

+------------+------------------------+---------------+
| Parameter  | Values                 | Default value |
+============+========================+===============+
| Set-action | mpls-exp-topmost <0-7> |               |
|            |                        |               |
|            | precedence <0-7> \|    |               |
|            |                        |               |
|            | dscp <0-63> \|         |               |
|            |                        |               |
|            | 802.1p <0-7>           |               |
|            |                        |               |
|            | qos-tag <0-7>          |               |
|            |                        |               |
|            | red-tag <0-1>          |               |
+------------+------------------------+---------------+
