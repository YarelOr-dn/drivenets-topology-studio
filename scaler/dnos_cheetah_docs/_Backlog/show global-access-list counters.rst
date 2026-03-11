show global-access-list counters - valid from v12
-------------------------------------------------

**Command syntax: show global-access-list counters**

**Description:** Displays global-access-list counters per rule. Command present a list of interfaces that global-ACL is assigned to

**CLI example:**
::

	dnRouter# show global-access-list counter
	Interface: bundle-1
	Access Lists  Ipv4
	Direction: in
	| Access-list name   | Index         | Type   | Protocol   | Src Ports   | Src IP   | Dest Ports   | Dest IP   | Matches |
	|--------------------+---------------+--------+------------+-------------+----------+--------------+-----------+---------|
	| MyAclName (global) | 10            | allow  | any        | any         | any      | any          | any       | 150     |
	|                    | 15            | deny   | icmp       | any         | 10.1.1.2 | any          | any       | 12      |
	|                    | default-icmp  | allow  | icmp       | any         | any      | any          | any       | 10000   |
	|                    | default       | deny   | any        | any         | any      | any          | any       | 2500128 |
	
	List of attached interfaces:
	bundle-1.21
	bundle-1.22
	bundle-2.21
	bundle-2.22
	bundle-3.21
	bundle-3.22
	
	
	Access Lists  Ipv6
	Direction: in
	| Access-list name   | Index          | Type   | Protocol   | Src Ports   | Src IP       | Dest Ports   | Dest IP   | Matches |
	|--------------------+----------------+--------+------------+-------------+--------------+--------------+-----------+---------|
	| MyAclName          | 10             | allow  | any        | any         | any          | any          | any       | 12      |
	|                    | 15             | deny   | icmp       | any         | 2001:1234::1 | any          | any       | 1       |
	|                    | default-icmp-v6| allow  | ipv6-icmp  | any         | any          | any          | any       | 23      |
	|                    | default        | deny   | any        | any         | any          | any          | any       | 2401    |
	
	List of attached interfaces:
	bundle-1.21
	bundle-1.22
	bundle-2.21
	bundle-2.22
	bundle-3.21
	bundle-3.22
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

Per rule counters presents matches **per all interfaces**

**Help line:** show global-access-list counters
