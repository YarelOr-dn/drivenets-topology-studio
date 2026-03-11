access-lists rule src-ip
------------------------

**Minimum user role:** operator

To create an access-list for the source IP, use the following command:

**Command syntax: rule [rule-id] [rule-type]** src-ip [src-ip]

**Command mode:** config

**Hierarchies**

- access-lists ipv4 rule

- access-lists ipv6 rule

**Note**

- The Source IP address format must match the access-list type (IPv4/IPv6).

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                     |                                                                                                                                                                                                                                                 |             |             |
| Parameter           | Description                                                                                                                                                                                                                                     | Range       | Default     |
+=====================+=================================================================================================================================================================================================================================================+=============+=============+
| rule-id             | The rule's unique identifier within the access-list. It determines the priority of the rule (rules with a low ID number have priority over rules with high ID numbers). You must configure at least one rule in order to create an access-list. |             |             |
|                     |                                                                                                                                                                                                                                                 | 1..65434    | 65535       |
|                     | The default ID (65535) is attached to the default access-list which is "Deny any".                                                                                                                                                              |             |             |
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
|                     |                                                                                                                                                                                                                                                 |             |             |
| src-ip              | The source IPs. Can be a specific host, a network   or group of hosts, or any host.                                                                                                                                                             | A.B.C.D/x   | Any         |
|                     |                                                                                                                                                                                                                                                 |             |             |
|                     |                                                                                                                                                                                                                                                 | x:x::x:x    |             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 101 allow src-ip 1.2.3.4/20
	dnRouter(cfg-acl-ipv4)# rule 102 deny src-ip 1.1.1.1/32
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow src-ip 2001:abcd::0/127


**Removing Configuration**

To delete a rule configuration:
::

	dnRouter(cfg-acl-ipv6)# no rule 200 allow src-ip

.. **Help line:** Configure access-lists rule source ip

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