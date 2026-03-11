policy match ip prefix
----------------------

**Minimum user role:** operator

To match routes based on IP address entries in the specified prefix-list:

**Command syntax: match ipv4|ipv6 prefix [prefix-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                                                                                                                 |                      |             |
| Parameter           | Description                                                                                                                                                                     | Range                | Default     |
+=====================+=================================================================================================================================================================================+======================+=============+
|                     |                                                                                                                                                                                 |                      |             |
| prefix-list-name    | The name of the prefix list from which to match   prefixes.                                                                                                                     | 1..255 characters    | \-          |
|                     |                                                                                                                                                                                 |                      |             |
|                     | You can match for both IPv4 and IPv6 prefix-list   under the same rule entry. The prefix-list type (ipv4 or ipv6) must match the   IP address family.                           |                      |             |
|                     |                                                                                                                                                                                 |                      |             |
|                     | Prefixes matching a "deny" rule in the   prefix-list (including the default rule) are considered as "no   match" in the policy and the next rule in the policy is evaluated.    |                      |             |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match ipv4 prefix PL_V4
	
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# match ipv6 prefix PL_v6


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no match ipv4 prefix
	dnRouter(cfg-rpl-policy-rule-10)# no match ipv6 prefix
	

.. **Help line:** Match routes based on IP address entries

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+