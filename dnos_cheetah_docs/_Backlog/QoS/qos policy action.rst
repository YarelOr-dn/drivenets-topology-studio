qos policy action
-----------------

**Command syntax: action**

**Description:** set actions for the matched traffic class

**TACACS role:** operator

**Note:**

This command enter to submode

no 'action' removes selected action's configuration.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy myPolicy1
	dnRouter(cfg-qos-policy-myPolicy1)# rule 1
	dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
	dnRouter(cfg-policy-myPolicy1-rule-1)# action 
	
	
**Command mode:** config qos policy rule

**Help line:** set rule actions
