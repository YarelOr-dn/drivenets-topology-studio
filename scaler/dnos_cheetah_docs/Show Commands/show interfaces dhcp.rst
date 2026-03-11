show interfaces dhcp
--------------------

**Minimum user role:** viewer

To display DHCP IP addresses for a specific interface:

**Command syntax:show interfaces dhcp** [interface-name]

**Command mode:** operational



**Note**

- The command is applicable to the following interface types:

	- mgmt0

	- mgmt-ncc


- Specify an interface to filter the displayed information to that interface.

**Parameter table**

+-------------------+----------------------------------------------------------------+-----------------+-------------+
| Parameter         | Description                                                    | Range           | Default     |
+===================+================================================================+=================+=============+
| interface-name    | Filters the displayed information to a specific interface      | mgmt0           | \-          |
|                   |                                                                | mgmt-ncc-0      |             |
|                   |                                                                | mgmt-ncc-1      |             |
+-------------------+----------------------------------------------------------------+-----------------+-------------+

**Example**
::

	dnRouter# show interfaces dhcp


	| Interface        | DHCP address | DHCP Server IP | Lease expires       |
	|------------------+--------------+----------------+---------------------|
	| mgmt0            | 172.16.1.4   | 172.16.1.4     | 2020-08-04 14:06:19 |
	| mgmt-ncc-0       | 172.16.1.4   | 172.16.1.4     | 2020-08-04 14:06:19 |


	dnRouter# show interfaces dhcp mgmt0

	Interface mgmt0
		Listening on: 84:4d:c0:7f:92:fc
		Bound IPv4 Address: 10.1.1.103/24
		IPv4 DHCP: enabled
		DHCPv4 addresses:
			DHCP Address: 10.1.1.103
				Client MAC: 84:4d:c0:7f:92:fc
				From Server: 10.1.1.100
				Lease starts: 2022-04-17 13:28:35
				Lease expires: 2022-04-17 13:38:35
				DHCPv4 options:
					‘DHCPv4 Option Code 67’: ‘test_bootfile’


.. **Help line:** show interfaces dhcp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
