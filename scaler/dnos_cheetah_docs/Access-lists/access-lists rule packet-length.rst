access-lists rule packet-length
--------------------------------

**Minimum user role:** operator

To create an access-list for the source ports, use the following command:

**Command syntax:** rule [rule-id] [rule-type] packet-length [min-length] [max-length]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- You can't configure more than 16 ingress ACL ranges across all attached ACLs (including IPv4 and IPv6 together) and across all types: source-port, dest-port and packet-length ranges.

- Packet-length match is not supported for egress ACLs.

- For IPv4 packets, in the IPv4 header field, this field is known as the Total Length.

- Total Length is the length of the datagram, measured in octets, including internet header and data.

- In IPv6 header field, this field is known as the Payload Length, the length of the IPv6 payload, i.e. the rest of the packet following the IPv6 header, in octets.

- When only min-length is present, it represents a specific length and eq operator is assumed to be default.

- When both min-length and max-length are specified, it implies a range inclusive of both values.

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
| min-length          | The minimum value. When only min-length is present, it represents a specific length and eq operator is assumed to be default.                                                                                                                   |  0-65535             | any         |
|                     |                                                                                                                                                                                                                                                 |                      |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                      |             |
| max-length          | The max value.  When both min-length and max-length are specified, it implies a range inclusive of both values.                                                                                                                                 | max-value>=min-value | \-          |
|                     |                                                                                                                                                                                                                                                 | max-value <= 65535   |             |
|                     |                                                                                                                                                                                                                                                 |                      |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 allow dest-ip 1.2.3.4/20 protocol tcp(0x06) src-ports 123 packet-length 100 200
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow protocol tcp(0x06) src-ports 100-200 packet-length 60 150
	dnRouter(cfg-acl-ipv6)# rule 300 deny packet-length 10000 65535
	dnRouter(cfg-acl-ipv6)# rule 300 deny packet-length 64
    dnRouter(cfg-acl-ipv6)# exit

**Removing Configuration**

To delete a rule configuration:
::

	dnRouter(cfg-acl-ipv6)# no rule 200 allow packet-length


.. **Help line:** Configure access-lists rule packet-length [min-length] [max-length]


**Command History**

+-------------+--------------------------+
|             |                          |
| Release     | Modification             |
+=============+==========================+
|             |                          |
| 17.0        | Command introduced       |
+-------------+--------------------------+
