access-lists rule fragmented
----------------------------

**Minimum user role:** operator

To create an access-list to match fragmented packets:

**Command syntax: rule [rule-id] [rule-type]** fragmented

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- This command is applicable to access-list-type IPv4 or IPv6. For IPv6, when setting a match for fragmented and IP protocol, protocol must be either tcp(0x06) or udp(0x11).

- A fragmented keyword can only be configured when an L4 header is not explicitly configured in an access-list.

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+-------------+
|                     |                                                                                                                                                                                                                                                 |               |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range         | Default     |
+=====================+=================================================================================================================================================================================================================================================+===============+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |               |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434      | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |               |             |
|                     |                                                                                                                                                                                                                                                 |               |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |               |             |
|                     |                                                                                                                                                                                                                                                 |               |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |               |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+-------------+
|                     | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                                                                                                                           |               |             |
| rule-type           |                                                                                                                                                                                                                                                 | allow         | \-          |
|                     |                                                                                                                                                                                                                                                 |               |             |
|                     |                                                                                                                                                                                                                                                 | deny          |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+-------------+
|                     |                                                                                                                                                                                                                                                 |               |             |
| fragmented          | Used to configure an access-list rule to match   fragmented packets.                                                                                                                                                                            | fragmented    | \-          |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 allow protocol icmp(0x01) icmp echo-reply ttl 0-10 fragmented


**Removing Configuration**

To delete a rule configuration:
::

	dnRouter(cfg-acl-ipv4)# no rule 101 allow fragmented


.. **Help line:** Configure access-lists fragmented flag

**Command History**

+-------------+-----------------------------+
|             |                             |
| Release     | Modification                |
+=============+=============================+
|             |                             |
| 5.1.0       | Command introduced          |
+-------------+-----------------------------+
|             |                             |
| 6.0         | Applied new hierarchy       |
+-------------+-----------------------------+
|             |                             |
| 13.0        | Updated support for IPv6    |
+-------------+-----------------------------+
