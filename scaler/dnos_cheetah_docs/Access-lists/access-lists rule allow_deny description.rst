access-lists rule allow/deny description
----------------------------------------

**Minimum user role:** operator

Add a description for the access-list action rule. The description is for information only. It is not installed in the data plane.

To add a rule description:

**Command syntax: rule [rule-id] [rule-type]** [description]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- The description rule occupies rule-id. It cannot share a rule-id with another allow/deny rule.


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                   |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range             | Default     |
+=====================+=================================================================================================================================================================================================================================================+===================+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |                   |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434          | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |                   |             |
|                     |                                                                                                                                                                                                                                                 |                   |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |                   |             |
|                     |                                                                                                                                                                                                                                                 |                   |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |                   |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| rule-type           |                                                                                                                                                                                                                                                 |                   |             |
|                     | Defines whether the traffic matching the rule   conditions are to be allowed or denied.                                                                                                                                                         | allow             | \-          |
|                     |                                                                                                                                                                                                                                                 |                   |             |
|                     |                                                                                                                                                                                                                                                 | deny              |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                   |             |
| description         | Add a description for the access-list rule.                                                                                                                                                                                                     | 256 characters    | \-          |
|                     |                                                                                                                                                                                                                                                 |                   |             |
|                     | Enter free-text description with spaces in   between quotation marks. If you do not use quotation marks, do not use   spaces. For example:                                                                                                      |                   |             |
|                     |                                                                                                                                                                                                                                                 |                   |             |
|                     | ... description "My long   description"                                                                                                                                                                                                         |                   |             |
|                     |                                                                                                                                                                                                                                                 |                   |             |
|                     | ... description   My_long_description                                                                                                                                                                                                           |                   |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+



**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 allow description "this is allow-all rule"
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv4)# rule 200 deny description this_is_deny_all_rule



**Removing Configuration**

To remove the description:
::

	dnRouter(cfg-acl-ipv6)# rule 200 deny description


.. **Help line:** Configure description rule

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| TBD         | Command introduced    |
+-------------+-----------------------+
