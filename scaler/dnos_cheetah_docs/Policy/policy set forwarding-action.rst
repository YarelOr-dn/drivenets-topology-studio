policy set forwarding-action
----------------------------

**Minimum user role:** operator

This command causes the system to ignore URPF check decision:

**Command syntax: set forwarding-action urpf-check ignore**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set forwarding-action urpf-check ignore


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set forwarding-action urpf-check ignore	


.. **Help line:** ignore urpf-check decision

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+