show access-lists counters in-band-management
---------------------------------------------

**Minimum user role:** viewer

Display control plane access-list counters per rule on the configured access lists. You can filter the information by access-list type (IPv4 or IPv6), to view all the IPv4 or IPv6 access-lists.


To display the access-list information:

**Command syntax: show access-lists counters in-band-management** [access-list-type]

**Command mode:** operational



**Note** 

- The command can be replaced with "show access-lists in-band management".

**Parameter table**

+------------------+-----------------------------------------------------+-------+---------+
| Parameter        | Description                                         | Range | Default |
+==================+=====================================================+=======+=========+
| access-list-type | Filter the displayed information to a specific type | IPv4  | \-      |
|                  |                                                     | IPv6  |         |
+------------------+-----------------------------------------------------+-------+---------+

The following information is displayed:

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
| Protocol         | The protocol specified in the rule                                                                         |
+------------------+------------------------------------------------------------------------------------------------------------+
| DSCP             | The DSCP value received on incoming packet                                                                 |
+------------------+------------------------------------------------------------------------------------------------------------+
| SRC/Dest Ports   | The source/destination ports specified in the rule                                                         |
+------------------+------------------------------------------------------------------------------------------------------------+
| SRC/Dest IP      | The source/destination IP specified in the rule                                                            |
+------------------+------------------------------------------------------------------------------------------------------------+
| Matches          | The number of packets that matched the rule (packets that were dropped by prior rules will not be counted) |
+------------------+------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show access-lists counters in-band-management
	Access Lists  Ipv4
	| Access-list name    | Index        | Type   | VRF        | Protocol                         | Src Ports   | Src IP            | Dest Ports   | Dest IP           | Dscp   | Matches   | Description   |
	|---------------------+--------------+--------+------------+----------------------------------+-------------+-------------------+--------------+-------------------+--------+-----------+---------------|
	| CP_ACL_IPv4         | 1            | allow  | CUST_A     | dsr(0x30)                        | any         | 18.134.129.55/26  | any          | 13.134.107.62/21  |        | 3         |               |
	| CP_ACL_IPv4         | 1            | allow  | CUST_A     | dsr(0x30)                        | any         | 18.134.129.55/26  | any          | 13.134.107.62/21  |        | 3         |               |
	| CP_ACL_IPv4         | 1            | allow  | CUST_A     | dsr(0x30)                        | any         | 18.134.129.55/26  | any          | 13.134.107.62/21  |        | 3         |               |
	| CP_ACL_IPv4         | 1            | allow  | CUST_A     | dsr(0x30)                        | any         | 18.134.129.55/26  | any          | 13.134.107.62/21  |        | 3         |               |
	|                     | 2            | deny   | CUST_A     | sscopmce(0x80)                   | any         | 12.32.68.26/29    | any          | 3.136.219.58/24   |        |           |               |
	|                     | 3            | allow  | CUST_A     | fc(0x85)                         | any         | 7.237.248.19/32   | any          | 12.146.60.26/20   |        |           |               |
	|                     | 4            | deny   | CUST_A     | 3pc(0x22)                        | any         | 19.103.111.160/28 | any          | 7.220.15.225/25   |        |           |               |
	|                     | 5            | deny   | CUST_A     | St(0x05)                         | any         | 13.44.26.233/23   | any          | 9.106.197.16/32   |        |           |               |
	|                     | 6            | deny   | CUST_B     | any-local-network(0x3F)          | any         | 15.27.24.201/30   | any          | 18.1.41.214/28    |        | 10        |               |
	|                     | 7            | deny   | CUST_B     | hmp(0x14)                        | any         | 16.32.187.53/23   | any          | 7.27.30.47/27     |        |           |               |
	|                     | 8            | allow  | CUST_B     | 3pc(0x22)                        | any         | 4.42.247.237/22   | any          | 17.25.246.17/23   |        |           |               |
	|                     | 9            | deny   | all        | micp(0x5F)                       | any         | 6.173.44.141/20   | any          | 5.48.50.82/31     |        |           |               |
	|                     | 10           | allow  | all        | iatp(0x75)                       | any         | 12.18.25.127/32   | any          | 2.106.119.126/21  |        |           |               |

	Access Lists  Ipv6
	| Access-list name    | Index           | Type   | VRF        | Protocol        | Src Ports   | Src IP   | Dest Ports   | Dest IP   | Traffic Class   | Matches   | Description   |
	|---------------------+-----------------+--------+------------+-----------------+-------------+----------+--------------+-----------+-----------------+-----------+---------------|
	| scale1-ingress-ipv6 | 2000            | allow  | all        | any             | any         | any      | any          | any       |                 | 92366     |               |
	|                     | default-icmp-v6 | allow  | CUST_A        | ipv6-icmp(0x3A) | any         | any      | any          | any       |                 |           |               |
	|                     | default         | deny   | all           | any             | any         | any      | any          | any       |                 |           |               |


	dnRouter# show access-lists counters in-band-management ipv4
	Access Lists  Ipv4
	| Access-list name    | Index        | Type   | VRF        | Protocol                         | Src Ports   | Src IP            | Dest Ports   | Dest IP           | Dscp   | Matches   | Description   |
	|---------------------+--------------+--------+------------+----------------------------------+-------------+-------------------+--------------+-------------------+--------+-----------+---------------|
	| CP_ACL_IPv4         | 1            | allow  | CUST_A     | dsr(0x30)                        | any         | 18.134.129.55/26  | any          | 13.134.107.62/21  |        | 3         |               |
	|                     | 2            | deny   | CUST_A     | sscopmce(0x80)                   | any         | 12.32.68.26/29    | any          | 3.136.219.58/24   |        |           |               |
	|                     | 3            | allow  | CUST_A     | fc(0x85)                         | any         | 7.237.248.19/32   | any          | 12.146.60.26/20   |        |           |               |
	|                     | 4            | deny   | CUST_A     | 3pc(0x22)                        | any         | 19.103.111.160/28 | any          | 7.220.15.225/25   |        |           |               |
	|                     | 5            | deny   | CUST_A     | St(0x05)                         | any         | 13.44.26.233/23   | any          | 9.106.197.16/32   |        |           |               |
	|                     | 6            | deny   | CUST_A     | any-local-network(0x3F)          | any         | 15.27.24.201/30   | any          | 18.1.41.214/28    |        | 10        |               |
	|                     | 7            | deny   | CUST_A     | hmp(0x14)                        | any         | 16.32.187.53/23   | any          | 7.27.30.47/27     |        |           |               |
	|                     | 8            | allow  | CUST_A     | 3pc(0x22)                        | any         | 4.42.247.237/22   | any          | 17.25.246.17/23   |        |           |               |
	|                     | 9            | deny   | CUST_A     | micp(0x5F)                       | any         | 6.173.44.141/20   | any          | 5.48.50.82/31     |        |           |               |
	|                     | 10           | allow  | all        | iatp(0x75)                       | any         | 12.18.25.127/32   | any          | 2.106.119.126/21  |        |           |               |

.. **Help line:** show access-lists counters in-band management

**Command History**

+---------+--------------------+
| Release | Modification       |
+---------+--------------------+
| 13.0    | Command introduced |
+---------+--------------------+

