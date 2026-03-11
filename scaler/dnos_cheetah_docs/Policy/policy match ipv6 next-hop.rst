policy match ipv6 next-hop
--------------------------

**Minimum user role:** operator

To match any IPv6 routes that have the specified next-hop router address or that match a next-hop address in the access lists:

**Command syntax: match ipv6 next-hop prefix-list [ipv6-prefix-list-name]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+--------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                          |                                                                                                                                                                                 |                      |             |
| Parameter                | Description                                                                                                                                                                     | Range                | Default     |
+==========================+=================================================================================================================================================================================+======================+=============+
|                          |                                                                                                                                                                                 |                      |             |
| ipv6-prefix-list-name    | Matches routes that have a next hop router   address in this access list.                                                                                                       | 1..255 characters    | \-          |
|                          |                                                                                                                                                                                 |                      |             |
|                          | Prefixes matching a "deny" rule in the   prefix-list (including the default rule) are considered as "no   match" in the policy and the next rule in the policy is evaluated.    |                      |             |
+--------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-10)# match ipv6 next-hop prefix-list PL6_TWAMP


**Removing Configuration**

To remove the match entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no match ipv6 next-hop


.. **Help line:** Match by a specific IPv6 next-hop address

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+