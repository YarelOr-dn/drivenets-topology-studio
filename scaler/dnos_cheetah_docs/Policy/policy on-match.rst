policy on-match
---------------

**Minimum user role:** operator

To jump to another rule in the policy or evaluate next attached policy:

**Command syntax: on-match {next \| goto [rule-id] \| next-policy}**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

..
	**Internal Note:**

	-  next - jump to the next configured rule

	-  goto - jump to a specific rule.

	   -  when the specified rule-id isn't configured, jump to the next higher configured rule

	   -  [rule-id] must be higher than the current rule id. e.g the following configuration in **invalid**

	   dnRouter# configure

	   dnRouter(cfg)# routing-policy

	   dnRouter(cfg-rpl)# policy POL_A

	   dnRouter(cfg-rpl-policy)# rule **20** allow

	dnRouter(cfg-rpl-policy-rule-  **20**)# goto **10**

	   ! can't jump backwards in policies

	- next-policy - evaluate next attached policy

		dnRouter# configure

		dnRouter(cfg)# routing-policy

		dnRouter(cfg-rpl)# policy MY_POLICY

		dnRouter(cfg-rpl-policy)# rule 10 allow

		dnRouter(cfg-rpl-policy-rule-10)# on-match next-policy


**Parameter table**

+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                   |                                                                                                                                                                     |             |             |
| Parameter         | Description                                                                                                                                                         | Range       | Default     |
+===================+=====================================================================================================================================================================+=============+=============+
|                   |                                                                                                                                                                     |             |             |
| next              | Jump to the next configured rule                                                                                                                                    | \-          | \-          |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                   |                                                                                                                                                                     |             |             |
| goto [rule-id]    | Jump to a specific rule. The rule-id must be higher than the current rule. Therefore, if you are configuring rule 20, you cannot configure on-match goto 10         | 1..65535    | \-          |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                   |                                                                                                                                                                     |             |             |
| next-policy       | Evaluate next attached policy                                                                                                                                       | \-          | \-          |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy POL_A
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# on-match next
	dnRouter(cfg-rpl-policy-rule-10)# exit
	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# on-match goto 30
	dnRouter(cfg-rpl-policy-rule-20)# exit
	dnRouter(cfg-rpl-policy)# rule 30 allow
    dnRouter(cfg-rpl-policy-rule-30)# on-match next-policy
	dnRouter(cfg-rpl-policy-rule-30)# match tag 10


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no on-match


.. **Help line:** Jump to another rule in the policy

**Command History**

+-------------+------------------------+
|             |                        |
| Release     | Modification           |
+=============+========================+
|             |                        |
| 6.0         | Command introduced     |
+-------------+------------------------+
|             |                        |
| 17.2        | next-policy introduced |
+-------------+------------------------+
