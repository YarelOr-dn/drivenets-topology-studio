access-lists rule src-ports
---------------------------

**Minimum user role:** operator

To create an access-list for the source ports, use the following command:

**Command syntax: rule [rule-id] [rule-type] protocol [protocol]** src-ports [source-ports]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- You can't configure more than 8 ingress IPv4 ACL source port ranges across all attached ACLs.

- You can't configure more than 8 ingress IPv6 ACL source port ranges across all attached ACLs.

- You can't configure more than 8 different IPv4 in-band-managment ACL source port ranges.

- You can't configure more than 8 different IPv6 in-band-managment ACL source port ranges

- For egress IPv4 ACL, you can't configure more than 24 unique combinations of SrcPortMin, SrcPortMax, DstPortMin, DstPortMax.

- Source port range is not supported for egress IPv6 ACL.

- If you remove the protocol field, the ports field will be removed.

**Parameter table:**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                      |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range                | Default     |
+=====================+=================================================================================================================================================================================================================================================+======================+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |                      |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434             | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |                      |             |
|                     |                                                                                                                                                                                                                                                 |                      |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |                      |             |
|                     |                                                                                                                                                                                                                                                 |                      |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |                      |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                      |             |
| rule-type           | Defines whether the traffic matching the rule conditions   are to be allowed or denied.                                                                                                                                                         | allow                | \-          |
|                     |                                                                                                                                                                                                                                                 |                      |             |
|                     |                                                                                                                                                                                                                                                 | deny                 |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                      |             |
| protocol            | The protocol used for the traffic.                                                                                                                                                                                                              | See protocol list    | \-          |
|                     |                                                                                                                                                                                                                                                 |                      |             |
|                     | You can enter the protocol name or use the   protocol ID. The protocol ID is displayed in hexadecimal next to each   protocol. You use the equivalent decimal value.                                                                            |                      |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                      |             |
| src-ports           | The source ports.                                                                                                                                                                                                                               | 0..65535             | Any         |
|                     |                                                                                                                                                                                                                                                 |                      |             |
|                     | Source ports can be configured as a range.                                                                                                                                                                                                      |                      |             |
|                     |                                                                                                                                                                                                                                                 |                      |             |
|                     | Source ports are supported only for protocol TCP   and UDP.                                                                                                                                                                                     |                      |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 allow dest-ip 1.2.3.4/20 protocol tcp(0x06) src-ports 123
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow protocol tcp(0x06) src-ports 100-200
	dnRouter(cfg-acl-ipv6)# rule 300 deny src-ip 2001::1 protocol udp(0x11) src-ports 179


**Removing Configuration**

To delete a rule configuration:
::

	dnRouter(cfg-acl-ipv6)# no rule 200 allow src-ports


.. **Help line:** Configure access-lists rule source ports


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