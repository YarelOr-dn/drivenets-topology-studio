access-lists rule
-----------------

**Minimum user role:** operator

For every access-list, you can set rules by defining attributes using the following syntax:

**Command syntax: rule [rule-id] [rule-type]**

**Command mode:** config

**Hierarchies**

- access-lists

**Note:**

- Access-list type can be ipv4 or ipv6. By default, rule without parameters relates to any value

- A rule with no parameters relates to any value.

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                     |                                                                                                                                                                                                                                                 |             |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range       | Default     |
+=====================+=================================================================================================================================================================================================================================================+=============+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |             |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434    | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any". See the default access-list in "show access-lists" on page 3297.                                                                                             |             |             |
|                     |                                                                                                                                                                                                                                                 |             |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |             |             |
|                     |                                                                                                                                                                                                                                                 |             |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |             |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                     |                                                                                                                                                                                                                                                 |             |             |
| rule-type           | Defines whether the traffic matching the rule   conditions are to be allowed or denied.                                                                                                                                                         | allow       | \-          |
|                     |                                                                                                                                                                                                                                                 |             |             |
|                     |                                                                                                                                                                                                                                                 | deny        |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

For every rule, you set an ID. The ID determines the positioning of the rule within the access-list (i.e. its priority). Every packet is checked against the rules by priority (from the lowest ID to the highest). The first rule that matches is applied. The rule ID is unique per access-list (not between access-lists).

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 description the next two rules are default rules
	dnRouter(cfg-acl-ipv4)# rule 102 allow
	dnRouter(cfg-acl-ipv4)# rule 103 deny
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow



**Removing Configuration**

To delete a rule:
::

	dnRouter(cfg-acl-ipv6)# no rule 200

To delete specific rule configuration:
::

	dnRouter(cfg-acl-ipv4)# no rule 102 deny

.. **Help line:** Configure access-lists rule

**Command History**

+-------------+---------------------------------------------------------------------------------------+
|             |                                                                                       |
| Release     | Modification                                                                          |
+=============+=======================================================================================+
|             |                                                                                       |
| 5.1.0       | Command introduced                                                                    |
+-------------+---------------------------------------------------------------------------------------+
|             |                                                                                       |
| 6.0         | Applied new hierarchy                                                                 |
+-------------+---------------------------------------------------------------------------------------+
|             |                                                                                       |
| 11.0        | Support of up to 2000 rules per access-list and   up to 250,000 rules per system.     |
+-------------+---------------------------------------------------------------------------------------+