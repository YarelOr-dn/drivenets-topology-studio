qos policy rule default
-----------------------

**Command syntax: rule default**

**Description:** Configure the default rule of the policy. rule-default can be configured with actions only.

It will match all the traffic that didn't hit the normal rules.

By default, if no queue is explicitly configured on rule-default, it is implicitly configured with a be (best-effort) queue

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy MyQoSPolicy1 
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule default 
	dnRouter(cfg-policy-MyQoSPOlicy1-rule-default)#
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# no rule default 
	
	
**Command mode:** config qos policy

**TACACS role:** operator

**Note:** rule default is created implicitly, also when the user doesn't explicitly configure it.

No command restores it to default (empty policy).

**Help line:** rule default
