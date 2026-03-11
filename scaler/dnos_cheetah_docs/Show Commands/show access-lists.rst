show access-lists
-----------------

**Minimum user role:** viewer

The show access-lists commands display information on the configured access lists. You can filter the information by access-list type (IPv4 or IPv6), to view all the IPv4 or IPv6 access-lists or by access-list name to view a specific access-list.


**Command syntax: show access-lists** [access-list-type] [access-list-name]

**Command mode:** operational


..
	**Internal Note**

	- When a user selects a specific type/access-list-name it will filter according to it

	- The user should be able to filter with several parameters on the same line. (filter by access-list-name)

**Parameter table**

+------------------+---------------------------------------------+-------------------------------------+---------+
| Parameter        | Description                                 | Range                               | Default |
+==================+=============================================+=====================================+=========+
| access-list-type | Filters displayed access-lists by type.     | IPv4                                | \-      |
|                  |                                             | IPv6                                |         |
+------------------+---------------------------------------------+-------------------------------------+---------+
| access-list-name | Filters the displayed access-lists by name. | The name of an existing access-list | \-      |
+------------------+---------------------------------------------+-------------------------------------+---------+

This command displays all the configured access-lists. The counters are displayed in the following order: per access-list > per rule. For each access-list, the following information is displayed:

+------------------+------------------------------------------------------------------------------------------------------------+
| Field            | Description                                                                                                |
+==================+============================================================================================================+
| Access-list name | The name of the access-list                                                                                |
+------------------+------------------------------------------------------------------------------------------------------------+
| Index            | The rule ID                                                                                                |
+------------------+------------------------------------------------------------------------------------------------------------+
| Type             | The type of rule (allow/deny)                                                                              |
+------------------+------------------------------------------------------------------------------------------------------------+
| Nexthop1         | A single next-hop ipv4/ipv6 address that is eligible for forwarding ipv4/ipv6 traffic                      |
+------------------+------------------------------------------------------------------------------------------------------------+
| Next-table       | The name of a vrf that should be used for forwarding the ipv4/ipv6 traffic matching the rule               |
+------------------+------------------------------------------------------------------------------------------------------------+
| Protocol         | The protocol specified in the rule                                                                         |
+------------------+------------------------------------------------------------------------------------------------------------+
| DSCP             | The DSCP value received on incoming packet                                                                 |
+------------------+------------------------------------------------------------------------------------------------------------+
| SRC/Dest Ports   | The source/destination ports specified in the rule                                                         |
+------------------+------------------------------------------------------------------------------------------------------------+
| SRC/Dest IP      | The source/destination IP specified in the rule                                                            |
+------------------+------------------------------------------------------------------------------------------------------------+
| Packet Length    | The IP packet length specified in the rule                                                                 |
+------------------+------------------------------------------------------------------------------------------------------------+
| Matches          | The number of packets that matched the rule (packets that were dropped by prior rules will not be counted) |
+------------------+------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show access-lists
	Access Lists  Ipv4
	| Access-list name   | Index           | Type         | Nexthop1  | Next Table | Protocol        | Src Ports  | Src IP       | Dest Ports  | Dest IP  | Dscp | Packet Length | Description       |
	|--------------------+-----------------+--------------+-----------+------------+-----------------+------------+--------------+-------------+----------|------+---------------+-------------------+
	| MyAclName (global) | 5               | description  |           |            |                 |            |              |             |          |      |               | allow UDP traffic |
	|                    | 10              | allow        |           |            | udp(0x11)       | any        | any          | any         | any      | any  |     any       |                   |
	|                    | 15              | deny         |           |            | all             | any        | 10.1.1.2     | any         | any      | any  |     any       |                   |
	|                    | 65000           | description  |           |            |                 |            |              |             |          |      |     any       | allowing ping     |
	|                    | default-icmp    | allow        |           |            | icmp(0x01)      | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	| MySecondACL        | 10              | allow        |           |            | tcp(0x06)       | 100-4500   | 10.1.1.2     | any         | any      | any  |     any       |                   |
	|                    | default-icmp    | allow        |           |            | icmp(0x01)      | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	| MyThirdACL         | 10              | allow        |           |            | tcp(0x06)       | 100-4500   | 20.1.1.2     | any         | any      | any  |     any       |                   |
	|                    | default-icmp    | allow        |           |            | icmp(0x01)      | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	| MyFourthACL        | 10              | allow        |           |            | tcp(0x06)       | 100-4500   | 30.1.1.2     | any         | any      | any  |     any       |                   |
	|                    | default-icmp    | allow        |           |            | icmp(0x01)      | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |


	Access Lists  Ipv6
	| Access-list name   | Index           | Type         | Nexthop1  | Next Table | Protocol        | Src Ports  | Src IP       | Dest Ports  | Dest IP  | Dscp | Packet Length | Description       |
	|--------------------+-----------------+--------------+-----------+------------+-----------------+------------+--------------+-------------+----------|------+---------------+-------------------+
	| MyAclName (global) | 10              | allow        |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	|                    | 15              | deny         |           |            | icmp(0x01)      | any        | 2001:1234::1 | any         | any      | any  |     any       |                   |
	|                    | default-icmp-v6 | allow        |           |            | ipv6-icmp(0x3A) | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	| MySecondACL        | 10              | allow        |           |            | tcp(0x06)       | 100-4500   | 1001::2222:2 | any         | any      | any  |     any       |                   |
	|                    | default-icmp-v6 | allow        |           |            | ipv6-icmp(0x3A) | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |

	dnRouter# show access-list ipv4
	Access Lists  Ipv4
	| Access-list name   | Index           | Type         | Nexthop1  | Next Table | Protocol        | Src Ports  | Src IP       | Dest Ports  | Dest IP  | Dscp | Packet Length | Description       |
	|--------------------+-----------------+--------------+-----------+------------+-----------------+------------+--------------+-------------+----------|------+---------------+-------------------+
	| MyAclName (global) | 10              | allow        |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	|                    | 15              | deny         |           |            | icmp(0x01)      | any        | 10.1.1.2     | any         | any      | any  |     any       |                   |
	|                    | default-icmp    | allow        |           |            | icmp(0x01)      | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	| MySecondACL        | 10              | allow        |           |            | tcp(0x06)       | 100-4500   | 10.1.1.2     | any         | any      | any  |     any       |                   |
	|                    | default-icmp    | allow        |           |            | icmp(0x01)      | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |


	dnRouter# show access-list ipv6
	Access Lists  Ipv6
	| Access-list name   | Index           | Type         | Nexthop1  | Next Table | Protocol        | Src Ports  | Src IP       | Dest Ports  | Dest IP  | Dscp | Packet Length | Description       |
	|--------------------+-----------------+--------------+-----------+------------+-----------------+------------+--------------+-------------+----------|------+---------------+-------------------+
	| MyAclName (global) | 10              | allow        |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	|                    | 15              | deny         |           |            | icmp(0x01)      | any        | 2001:1234::1 | any         | any      | any  |     any       |                   |
	|                    | default-icmp-v6 | allow        |           |            | ipv6-icmp(0x3A) | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |
	| MySecondACL        | 10              | allow        |           |            | tcp(0x06)       | 100-4500   | 1001::2222:2 | any         | any      | any  |     any       |                   |
	|                    | default-icmp-v6 | allow        |           |            | ipv6-icmp(0x3A) | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |


	dnRouter# show access-list MySecondACL
	Access Lists  Ipv4
	| Access-list name   | Index           | Type         | Nexthop1  | Next Table | Protocol        | Src Ports  | Src IP       | Dest Ports  | Dest IP  | Dscp | Packet Length | Description       |
	|--------------------+-----------------+--------------+-----------+------------+-----------------+------------+--------------+-------------+----------|------+---------------+-------------------+
	| MySecondACL        | 10              | allow        |           |            | tcp(0x06)       | 100-4500   | 10.1.1.2     | any         | any      | any  |     any       |                   |
	|                    | default-icmp    | allow        |           |            | icmp(0x01)      | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |

	Access Lists  Ipv6
	| Access-list name   | Index           | Type         | Nexthop1  | Next Table | Protocol        | Src Ports  | Src IP       | Dest Ports  | Dest IP  | Dscp | Packet Length | Description       |
	|--------------------+-----------------+--------------+-----------+------------+-----------------+------------+--------------+-------------+----------|------+---------------+-------------------+
	| MySecondACL        | 10              | allow        |           |            | tcp(0x06)       | 100-4500   | 1001::2222:2 | any         | any      | any  |     any       |                   |
	|                    | default-icmp-v6 | allow        |           |            | ipv6-icmp(0x3A) | any        | any          | any         | any      | any  |     any       |                   |
	|                    | default         | deny         |           |            | any             | any        | any          | any         | any      | any  |     any       |                   |


.. **Help line:** show access-list information

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 5.1.0   | Command introduced                              |
+---------+-------------------------------------------------+
| 13.0    | Updated show output to support DSCP and Nexthop |
+---------+-------------------------------------------------+
| 16.2    | Updated show output to support Next Table       |
+---------+-------------------------------------------------+
| 17.0    | Updated show output to support length-range     |
+---------+-------------------------------------------------+
