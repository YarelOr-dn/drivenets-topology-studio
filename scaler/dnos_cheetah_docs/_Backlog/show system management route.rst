show system management route - deprecated
-----------------------------------------

**Command syntax: show system management route**

**Description:** shows static route configuration on management eth0 interface of the active controller (RE).

**CLI example:**
::

	dnRouter# show system management route
	Legend: S - static,
	        > - Selected route, * - Installed route
	
	IPv4 Route Table:
	| Flags       | IP Prefix        | Next Hop           | Resolved Next Hop | Interface    |
	|-------------+------------------+--------------------+-------------------+--------------|
	| S>* [5/0]   | 12.2.2.2/32      | 30.1.1.2           |                   | mgmt0          |
	
	IPv6 Route Table:
	| Flags       | IP Prefix        | Next Hop           | Resolved Next Hop | Interface    |
	|-------------+------------------+--------------------+-------------------+--------------|
	| S>* [110/0] | 2001:1235::0/122 | 2001:1235::1       |                   | mgmt0          |
	
	 
	dnRouter(cfg)# system management route ipv4 
	Legend: C - connected, S - static,
	        > - Selected route, * - Installed route
	
	IPv4 Route Table:
	| Flags       | IP Prefix      | Next Hop   | Resolved Next Hop | Interface    |
	|-------------+----------------+------------+-------------------+--------------|
	| S>* [5/0]   | 12.2.2.2/32    | 30.1.1.2   |                   | mgmt0          |
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:** By default, the command output displays ipv4 & ipv6 routing

**Help line:** show management route table

+---------------+----------------------+---------------+
| Parameter     | Values               | Default value |
+===============+======================+===============+
| ipv4-prefix   | {ipv4-prefix format} |               |
+---------------+----------------------+---------------+
| ipv6-prefix   | {ipv6-prefix format} |               |
+---------------+----------------------+---------------+
| interface     | mgmt0                |               |
+---------------+----------------------+---------------+
| protocol-name | static               |               |
+---------------+----------------------+---------------+
