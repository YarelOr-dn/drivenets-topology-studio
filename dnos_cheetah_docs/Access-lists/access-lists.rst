access-lists
------------

**Minimum user role:** operator

Access-lists commands are hierarchical. You can create multiple access-lists with multiple rules in each access-list. To configure an access-list:

**Command syntax: access-lists [access-list_type] [access-list_name]**

**Command mode:** config

**Hierarchies**

- configuration

**Note**

- You cannot configure an access-lists with a reserved name (e.g., ipv4, ipv6, counters, interface name).

- You cannot delete an access-list that is associated with an interface.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|                     |                                                                                                                                                                                                                                              |           |             |
| Parameter           | Description                                                                                                                                                                                                                                  | Range     | Default     |
+=====================+==============================================================================================================================================================================================================================================+===========+=============+
|                     |                                                                                                                                                                                                                                              |           |             |
| access-list-type    |  The type of access-list   that you are configuring (IPv4 or IPv6)                                                                                                                                                                           | IPv4      | \-          |
|                     |                                                                                                                                                                                                                                              |           |             |
|                     |                                                                                                                                                                                                                                              | IPv6      |             |
+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|                     |                                                                                                                                                                                                                                              |           |             |
| access-list-name    | The specific access-list that you want to configure. All rules   that are created using the same access-list name belong to the same   access-list. If you use a different access-list name for a rule, a new   access-list will be created. | Text      | \-          |
|                     |                                                                                                                                                                                                                                              |           |             |
|                     | You cannot configure an access-list with a reserved name (ipv4,   ipv6, counters, interface name).                                                                                                                                           |           |             |
|                     |                                                                                                                                                                                                                                              |           |             |
|                     | You can configure up to 10,000 access-lists per system.                                                                                                                                                                                      |           |             |
+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 100 allow src-ip any dest-ip any
	dnRouter(cfg-acl-ipv4)# rule 101 allow src-ip 1.2.3.4/20
	dnRouter(cfg-acl-ipv4)# rule 102 deny dest-ip 1.1.1.1/32 protocol tcp(0x06) src-ports 100-200
	dnRouter(cfg-acl-ipv4)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_1
	dnRouter(cfg-acl-ipv6)# rule 100 allow protocol udp(0x11)
	dnRouter(cfg-acl-ipv6)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow src-ip 2001:abcd::0/127
	dnRouter(cfg-acl-ipv6)# rule 200 allow protocol tcp
	dnRouter(cfg-acl-ipv6)# exit

	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# ipv6 MyAccess_list_3
	dnRouter(cfg-acl-ipv6)# rule 300 deny dest-ip 2001:abcd::0/127
	dnRouter(cfg-acl-ipv6)# exit

	dnRouter(cfg)# no access-lists
	dnRouter(cfg-acl)# no ipv6
	dnRouter(cfg-acl)# no ipv6 MyAccess-list-1

	dnRouter(cfg-acl-ipv4)# MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# no rule 100



**Removing Configuration**

To delete all access-lists:
::

	dnRouter(cfg)# no access-lists

To delete all IPv4 access lists:
::

	dnRouter(cfg)# no ipv4

To delete a specific access list:
::

	dnRouter(cfg)# no ipv4 MyAccess_list_1

..
	validation:

	| if a user tries to remove an access-list while it is attached to an interface the following error should be displayed:
	
	| "Error: failed to remove access-list <access-list-name>. access-list is attached to interface <interface-name>.

	Rule parameters restrictions:

	-  ICMP option is available only for ICMP protocol

	-  ICMP-v6 option is available only for IPv6-ICMP protocol

	-  TCP-flag option is available only for TCP protocol

	-  Hop-limit option is available only for ipv6 access-list type

	-  IPv4-options option is available only for ipv4 access-list type

	-  Src-ports/dest-ports are available only for protocol type TCP or UDP

	for each access-list configuration:

	-  rule id 65535 will be "default" - operation deny on any protocols, ip's and ports. this rule is lowest rule in the table

	-  rule id 65534 will be "default-icmp" for ipv4 type of acl - operation allow on protocol type icmp-v4 on any ip's and ports. this rule is only above "default" rule and below the other rules.

	-  rule id 65534 will be "default-icmp-v6" for ipv6 type of acl - operation allow on protocol type icmp-v6 on any ip's and ports. this rule is only above "default" rule and below the other rules.



	Scale validation:

	-  up to 2K rules per ACL

	-  up to 10K ACLs per system

	-  up to 250K rules per system

	-  up to 50K ingress ACL rules per NCP - ACLs are attached to interfaces (in direction)

	-  up to 20K egress ACL rules per NCP - ACLs are attached to interfaces (out direction) - egress ACL is supported starting from v11.1

	when the limit reached, comit will be rejected and the CLI will prompt (according the limit):

	"Error :Failed to set access-list <name> rule <id>. Number of rules for access-list has reached the maximum limit capacity per ACL"

	"Error :Failed to set access-list <name> rule <id>. Number of rules for access-list has reached the maximum limit capacity for system"

	"Error: Failed to set access-list <name>. Number of access-lists for system has reached the maximum limit capacity for system.

	"Error: Failed to attach access-list <name> to interface <id> direction <direction>. Number of access-list rules for system has reached the maximum limit capacity per NCP.

.. **Help line:** Configure access-lists

**Command History**

+-------------+----------------------------------------------------------------------------+
|             |                                                                            |
| Release     | Modification                                                               |
+=============+============================================================================+
|             |                                                                            |
| 5.1.0       | Command introduced                                                         |
+-------------+----------------------------------------------------------------------------+
|             |                                                                            |
| 6.0         | Applied   new hierarchyReplaced access-list with access-lists in syntax    |
+-------------+----------------------------------------------------------------------------+