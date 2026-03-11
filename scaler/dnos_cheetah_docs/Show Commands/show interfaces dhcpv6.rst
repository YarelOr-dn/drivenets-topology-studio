show interfaces dhcpv6
----------------------

**Minimum user role:** viewer

The command displays DHCPv6 IP addresses for a specific interface.

**Command syntax:show interfaces dhcpv6** [interface-name]

**Command mode:** operational



**Note**

- The command is applicable to the following interface types:

	- mgmt0

	- mgmt-ncc

	- Physical

	- Physical VLAN

	- Bundle

	- Bundle VLAN


- Specify an interface to filter the displayed information to that interface.

**Parameter table**

+----------------+-----------------------------------------------------------+-----------------------------------------------------------------------------+-----------+
| Parameter      | Description                                               | Range                                                                       | Default   |
+================+===========================================================+=============================================================================+===========+
| interface-name | Filters the displayed information to a specific interface | mgmt0, mgmt-ncc-0, mgmt-ncc-1, geX-X/X/X, geX-X/X/X.Y, bundle-X, bundle-X.Y | \-        |
+----------------+-----------------------------------------------------------+-----------------------------------------------------------------------------+-----------+

**Example**
::

	dnRouter# show interfaces dhcpv6

	| Interface            | DHCP address   | DHCP Server DUID   | Lease expires       |
	+----------------------+----------------+--------------------+---------------------+
	| ge100-0/0/0.200      | CAFE::1/24     | CAFE::D            | 2020-07-19 15:09:47 |
	| mgmt0                | CAFE::1/24     | CAFE::D            | 2020-07-19 14:05:43 |
	| mgmt-ncc-0           | CAFE::2/24     | CAFE::D            | 2020-07-19 14:10:20 |
	| mgmt-ncc-1           | CAFE::3/24     | CAFE::D            | 2020-07-19 14:10:23 |
  

	dnrouter# sh int dhcpv6 mgmt0

	Interface mgmt0
		Listening on: 84:4d:c0:7f:92:fc
		Bound IPv6 Address: 2001:db8:0:1::254/128
		Bound IPv6 Local Address: fe80::864d:c0ff:fe7f:92fc/64
		IPv6 DHCP: enabled
		DHCPv6 addresses:
			DHCPv6 Address: 2001:db8:0:1::254
				Client MAC: 84:4d:c0:7f:92:fc
				From Server: 0001000129f2c2c516a86786a6cd
				Lease starts:  2022-04-20 14:02:28
				Lease expires: 2022-04-20 14:12:28
				DHCPv6 options:
					N/A


.. **Help line:** show interfaces dhcpv6

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 13.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 19.1    | Extended support for in-band network interfaces |
+---------+-------------------------------------------------+