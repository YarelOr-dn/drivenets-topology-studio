access-lists rule icmp
-----------------------

**Minimum user role:** operator

To create an access-list for the ICMP protocol, use the following command:

**Command syntax: rule [rule-id] [rule-type] protocol icmp(0x01)** icmp-type [message-type]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- ICMP message-type are available only for ICMP (ipv4) protocol


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                             |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range                       | Default     |
+=====================+=================================================================================================================================================================================================================================================+=============================+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |                             |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434                    | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |                             |             |
|                     |                                                                                                                                                                                                                                                 |                             |             |
|                     | Rule ID 65534 is reserved for default-icmp for IPv4/IPv6 access-lists, which allows protocol type icmp-v4/icmp-v6 on any IP and port.                                                                                                           |                             |             |
|                     |                                                                                                                                                                                                                                                 |                             |             |
|                     | You can configure up to 2000 rules per access-list and up to 250,000 rules altogether per system.                                                                                                                                               |                             |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+-------------+
|                     | Defines whether the traffic matching the rule conditions are to be allowed or denied.                                                                                                                                                           |                             |             |
| rule-type           |                                                                                                                                                                                                                                                 | allow                       | \-          |
|                     |                                                                                                                                                                                                                                                 |                             |             |
|                     |                                                                                                                                                                                                                                                 | deny                        |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+-------------+
|                     |                                                                                                                                                                                                                                                 |                             |             |
| icmp                | Used to configure an access-list rule to match a specific ICMP message type.                                                                                                                                                                    | See ICMP message   types    | \-          |
|                     |                                                                                                                                                                                                                                                 |                             |             |
|                     | Applicable only to ICMP protocol.                                                                                                                                                                                                               |                             |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+-------------+

**ICMP message types**

+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| Keyword (string)                          | RFC type number | RFC code number | Meaning                                                           |
+===========================================+=================+=================+===================================================================+
| echo-reply                                | 0               | 0               | Echo Reply                                                        |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| destination-network-unreachable           | 3               | 0               | Destination unreachable-Destination network unreachable           |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| destination-host-unreachable              | 3               | 1               | Destination unreachable-Destination host unreachable              |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| destination-protocol-unreachable          | 3               | 2               | Destination unreachable-Destination protocol unreachable          |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| destination-port-unreachable              | 3               | 3               | Destination unreachable-Destination port unreachable              |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| fragmentation-required                    | 3               | 4               | Destination unreachable-Fragmentation required                    |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| source-route-failed                       | 3               | 5               | Destination unreachable-Source route failed                       |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| destination-network-unknown               | 3               | 6               | Destination unreachable-Destination network unknown               |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| destination-host-unknown                  | 3               | 7               | Destination unreachable-Destination host unknown                  |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| source-host-isolated                      | 3               | 8               | Destination unreachable-Source host isolated                      |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| network-administratively-prohibited       | 3               | 9               | Destination unreachable-Network administratively prohibited       |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| host-administratively-prohibited          | 3               | 10              | Destination unreachable-Host administratively prohibited          |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| network-unreachable-for-tos               | 3               | 11              | Destination unreachable-Network unreachable for ToS               |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| host-unreachable-for-tos                  | 3               | 12              | Destination unreachable-Host unreachable for ToS                  |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| communication-administratively-prohibited | 3               | 13              | Destination unreachable-Communication administratively prohibited |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| host-precedence-violation                 | 3               | 14              | Destination unreachable-Host Precedence Violation                 |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| precedence-cutoff-in-effect               | 3               | 15              | Destination unreachable-Precedence cutoff in effect               |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| redirect-network                          | 5               | 0               | Redirect Datagram-for the Network                                 |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| redirect-host                             | 5               | 1               | Redirect Datagram-for the Host                                    |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| redirect-tos-network                      | 5               | 2               | Redirect Datagram-for the ToS and network                         |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| redirect-tos-host                         | 5               | 3               | Redirect Datagram-for the ToS and host                            |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| echo-request                              | 8               | 0               | Echo Request                                                      |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| router-advertisement                      | 9               | 0               | Router Advertisement                                              |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| router-solicitation                       | 10              | 0               | Router Solicitation                                               |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| ttl-expired-in-transit                    | 11              | 0               | Time Exceeded-TTL expired in transit                              |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| fragment-reassembly                       | 11              | 1               | Time Exceeded-Fragment reassembly                                 |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| pointer-indicates-error                   | 12              | 0               | Parameter Problem-Pointer indicates error                         |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| missing-required-option                   | 12              | 1               | Parameter Problem-Missing required option                         |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| bad-length                                | 12              | 2               | Parameter Problem-Bad length                                      |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| timestamp                                 | 13              | 0               | Timestamp                                                         |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+
| timestamp-reply                           | 14              | 0               | Timestamp-Reply                                                   |
+-------------------------------------------+-----------------+-----------------+-------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 100 allow protocol icmp(0x01) icmp-type echo-request
	dnRouter(cfg-acl-ipv4)# rule 101 allow protocol icmp(0x01) icmp-type echo-reply



**Removing Configuration**

To delete a rule configuration, the protocol value must be specific:
::

	dnRouter(cfg-acl-ipv4)# no rule 101 allow icmp-type

.. **Help line:** Configure access-lists rule icmp message type

**Command History**

+-------------+----------------------------------+
|             |                                  |
| Release     | Modification                     |
+=============+==================================+
|             |                                  |
| 5.1.0       | Command introduced               |
+-------------+----------------------------------+
|             |                                  |
| 6.0         | Applied new hierarchy            |
+-------------+----------------------------------+
|             |                                  |
| 9.0         | Not supported in this version    |
+-------------+----------------------------------+
|             |                                  |
| 11.0        | Command reintroduced             |
+-------------+----------------------------------+
