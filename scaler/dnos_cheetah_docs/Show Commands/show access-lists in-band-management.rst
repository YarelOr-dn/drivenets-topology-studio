show access-lists in-band-management
------------------------------------

**Minimum user role:** viewer

To display the control plane access-lists and the matching counters per rule:



**Command syntax: show access-lists in-band-management** [access-list-type] [access-list-name]

**Command mode:** operational


..
	**Internal Note**

	- When a user selects a specific type/access-list-name it will filter according to it

	- The user should be able to filter with several parameters on the same line. (filter by access-list-name)


**Parameter table**

+------------------+------------------------------------------------------------+-------------------------------------+---------+
| Parameter        | Description                                                | Range                               | Default |
+==================+============================================================+=====================================+=========+
| access-list-type | Filter the displayed information to a specific type        | IPv4                                | \-      |
|                  |                                                            | IPv6                                |         |
+------------------+------------------------------------------------------------+-------------------------------------+---------+
| access-list-name | Filter the displayed information to a specific access-list | The name of an existing access-list |         |
+------------------+------------------------------------------------------------+-------------------------------------+---------+

The following information is displayed in the table:

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

	dnRouter# show access-lists in-band-management

	Access Lists - Ipv4

	| Access-list name      | Index        | Type   | VRF        | Protocol                         | Src Ports   | Src IP            | Dest Ports   | Dest IP           | Dscp   | Description   |
	|-----------------------+--------------+--------+------------+----------------------------------+-------------+-------------------+--------------+-------------------+--------+---------------|
	| CP_ACL_IPv4           | 10           | allow  | CUST_A     | any                              | any         | 100.64.0.0/20     | any          | any               |        |               |
	|                       | 20           | allow  | CUST_A     | any                              | any         | 100.64.200.0/24   | any          | any               |        |               |
	|                       | default-icmp | allow  | all        | icmp(0x01)                       | any         | any               | any          | any               |        |               |
	|                       | default      | deny   | all        | any                              | any         | any               | any          | any               |        |               |

	Access Lists - Ipv6

	| Access-list name   | Index   | Type   | VRF        | Protocol   | Src Ports   | Src IP   | Dest Ports   | Dest IP   | Traffic Class   | Description   |
	|--------------------+---------+--------+------------+------------+-------------+----------+--------------+-----------+-----------------+---------------|

	dnRouter# show access-lists in-band-management ipv4

	dnRouter# show access-lists in-band-management ipv4 CP_ACL_IPv4

	dnRouter# show access-lists in-band-management CP_ACL_IPv6


.. **Help line:** show control plane inbaband access-lists

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


