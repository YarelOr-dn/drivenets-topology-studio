access-lists rule ipv4-options
------------------------------

**Minimum user role:** operator

When configured, the ACCESS-LISTS rule validates if the ipv4-options header field exist in the packet IPv4 header. To create an access-list to match the IPv4-options header field:

**Command syntax: rule [rule-id] [rule-type]** ipv4-options

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- The ipv4-options parameter is available only for access-list type IPv4.

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
|                     | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                                                                                                                           |                 |             |
| rule-type           |                                                                                                                                                                                                                                                 | allow           | \-          |
|                     |                                                                                                                                                                                                                                                 |                 |             |
|                     |                                                                                                                                                                                                                                                 | deny            |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                 |             |
| ipv4-options        | Used to configure an access-list rule to match   the existence of ipv4-options header field in the IPv4 packet's header.                                                                                                                        | IPv4 options    | \-          |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 100 allow ipv4-options
	dnRouter(cfg-acl-ipv4)# rule 101 allow protocol icmp(0x01) ipv4-options


**Removing Configuration**

To delete the access-list rule configuration:
::

	dnRouter(cfg-acl-ipv4)# no rule 101 allow ipv4-options


.. **Help line:** Configure access-lists rule protocol

**Command History**

+-------------+--------------------------+
|             |                          |
| Release     | Modification             |
+=============+==========================+
|             |                          |
| 5.1.0       | Command introduced       |
+-------------+--------------------------+
|             |                          |
| 6.0         | Applied new hierarchy    |
+-------------+--------------------------+