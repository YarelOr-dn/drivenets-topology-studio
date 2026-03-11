show system dns
---------------

**Minimum user role:** viewer

To display all configured DNS parameters:



**Command syntax: show system dns**

**Command mode:** operational



**Parameter table**

+------------------+-----------------------------------------------------------------------------------------------------------+--------------+
| Parameter        | Description                                                                                               | Range        |
+==================+===========================================================================================================+==============+
| DNS lookup       | The admin-state of the DNS lookup functionality                                                           | Enabled      |
|                  |                                                                                                           | Disabled     |
+------------------+-----------------------------------------------------------------------------------------------------------+--------------+
| DNS timeout      | The amount of time (in seconds) to wait for a response to a DNS query (not configurable)                  | 5            |
+------------------+-----------------------------------------------------------------------------------------------------------+--------------+
| DNS retry        | The number of times to retry sending DNS queries (not configurable)                                       | 3            |
+------------------+-----------------------------------------------------------------------------------------------------------+--------------+
| Domain name      | The domain name that DNOS uses to complete unqualified hostnames.                                         | String       |
+------------------+-----------------------------------------------------------------------------------------------------------+--------------+
| DNS servers list | The list of the DNS servers used. DNS servers can derive both from configuration and from the DHCP server | IPv4 Address |
|                  |                                                                                                           | IPv6 Address |
+------------------+-----------------------------------------------------------------------------------------------------------+--------------+

**Example**
::

	dnRouter# show system dns 
	
	Inband 
	
	DNS lookup: enabled
	DNS timeout: 5 seconds
	DNS retry: 3
	Domain name: fgh.com
	
	DNS servers:
	
	vrf default DNS servers:

	Statically configured DNS servers:

	| Priority | IP address   | Admin State |
	|----------+--------------+-------------|
	| 1        | 11.1.1.20    | Enabled     |
	| 2        | 1111::1      | Enabled     |
	| 3        | 11.1.1.22    | Disabled    |


	DHCP acquired DNS servers:

	| Priority | IP address   |
	|----------+--------------|
	| 7        | 11.1.1.30    |
	| 8        | 11.1.1.32    |
	| 9        | 55:66:77::1  |


	vrf mgmt0 DNS servers:

	Statically configured DNS servers:

	| Priority | IP address   | Admin State |
	|----------+--------------+-------------|
	| 4        | 10.1.1.20    | Enabled     |
	| 5        | 10.1.1.22    | Enabled     |
	| 6        | 1234:1234::1 | Disabled    |
	

	DHCP acquired DNS servers:

	| Priority | IP address   |
	|----------+--------------|
	| 10       | 10.1.1.30    |
	| 11       | 10.1.1.32    |
	| 12       | 9876:65::1   |


	vrf non-default-vrf DNS servers:

	Statically configured DNS servers:

	| Priority | IP address   | Admin State |
	|----------+--------------+-------------|
	| 4        | 10.1.1.20    | Enabled     |
	| 5        | 10.1.1.22    | Enabled     |
	| 6        | 1234:1234::1 | Disabled    |


.. **Help line:** show all configured DNS parameters

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 11.0    | Command introduced                        |
+---------+-------------------------------------------+
| 15.1    | Added support for IPv6 Address format     |
+---------+-------------------------------------------+
| 19.1    | Support non default inband management vrf |
+---------+-------------------------------------------+

