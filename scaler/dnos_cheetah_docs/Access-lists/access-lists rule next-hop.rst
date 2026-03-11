access-lists rule next-hop
--------------------------

**Minimum user role:** operator

You can define to route certain traffic through specific paths other than those defined by routing protocols. This can be achieved by specifying the next-hop address in access-lists configurations, so that the configured next-hop address from the access-list is used for forwarding packets towards its destination. This is instead of routing packet-based destination address lookup. If the configured next-hop is unreachable, the packets matching the rule will be forwarded according to the regular FIB lookup of the destination IP.

Next-hop configuration for forwarding packets is referred to as ACL Based Forwarding (ABF).

To configure the next-hop IP address to which packets matching the rule will be redirected:

**Command syntax: rule [rule-id] allow** next-hop1 [next-hop]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- Next-hop action is allowed only for rule of type allow.

- Next-hop IP address type format is validated against the access-list type (IPv4/IPv6).

- Next-hop IP address must not match any of the router local addresses.

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                 |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range           | Default     |
+=====================+=================================================================================================================================================================================================================================================+=================+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |                 |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434        | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |                 |             |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |                 |             |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |                 |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     | Defines whether the traffic matching the rule   conditions are to be allowed or denied.                                                                                                                                                         |                 |             |
| rule-type           |                                                                                                                                                                                                                                                 | allow           | \-          |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     |                                                                                                                                                                                                                                                 | deny            |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                 |             |
| next-hop            | The next-hop IP address to which packets matching the rule are redirected.                                                                                                                                                                      | A.B.C.D         | \-          |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     | The next-hop IP address must not match any of the router's local IP addresses.                                                                                                                                                                  | xx:xx::xx:xx    |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 allow next-hop1 1.2.3.4
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow next-hop1 2001:abcd::1

	dnRouter(cfg-acl-ipv4)# no rule 101 allow next-hop1
	dnRouter(cfg-acl-ipv6)# no rule 200 allow next-hop1

**Removing Configuration**

To remove the rule configuration:
::

	dnRouter(cfg-acl-ipv6)# no rule 101 allow next-hop1

.. **Help line:** Configure access-lists rule destination IP

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+
