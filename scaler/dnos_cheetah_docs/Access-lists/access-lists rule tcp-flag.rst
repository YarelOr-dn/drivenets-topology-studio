access-lists rule tcp-flag
--------------------------

**Minimum user role:** operator

To create an access-list to match TCP flags, use the following command:

**Command syntax: rule [rule-id] [rule-type] protocol tcp(0x06)** tcp-flag [list of tcp-flags]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                         |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range                   | Default     |
+=====================+=================================================================================================================================================================================================================================================+=========================+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |                         |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434                | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |                         |             |
|                     |                                                                                                                                                                                                                                                 |                         |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |                         |             |
|                     |                                                                                                                                                                                                                                                 |                         |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |                         |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                         |             |
| rule-type           | Defines whether the traffic matching the rule   conditions are to be allowed or denied.                                                                                                                                                         | allow                   | \-          |
|                     |                                                                                                                                                                                                                                                 |                         |             |
|                     |                                                                                                                                                                                                                                                 | deny                    |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+
|                     |                                                                                                                                                                                                                                                 | See TCP flag list below |             |
| tcp-flag            | Used to configure an access-list rule to match   specific TCP flags.                                                                                                                                                                            |                         | \-          |
|                     |                                                                                                                                                                                                                                                 |                         |             |
|                     | Multiple tcp-flag can be configured per rule. In   this case all flags must be matched for the rule to apply.                                                                                                                                   |                         |             |
|                     |                                                                                                                                                                                                                                                 |                         |             |
|                     | Available for TCP protocol only.                                                                                                                                                                                                                |                         |             |
|                     |                                                                                                                                                                                                                                                 |                         |             |
|                     | Not supported by egress IPv6 access-lists; the   policy will be rejected if attached in out   direction                                                                                                                                         |                         |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------+-------------+

**TCP flag table**

+------------------+
| Keyword (string) |
+==================+
| urg              |
+------------------+
| ack              |
+------------------+
| psh              |
+------------------+
| rst              |
+------------------+
| syn              |
+------------------+
| fin              |
+------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_1
	dnRouter(cfg-acl-ipv6)# rule 101 allow dest-ip 1.2.3.4/20 protocol tcp(0x06) tcp-flag syn
	dnRouter(cfg-acl-ipv6)# rule 102 deny protocol tcp(0x06) dest-ports 300 tcp-flag syn ack
	dnRouter(cfg-acl-ipv6)# rule 102 deny protocol tcp(0x06) dest-ports 300 tcp-flag fin ack


**Remove Configuration**

To delete a rule configuration:
::

	dnRouter(cfg-acl-ipv6)# no rule 102 allow tcp-flag


.. **Help line:** Configure access-list rule tcp-flag

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
