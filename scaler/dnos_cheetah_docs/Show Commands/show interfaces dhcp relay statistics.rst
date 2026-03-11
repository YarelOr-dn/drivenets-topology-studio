show interfaces dhcp relay statistics
-------------------------------------

**Minimum user role:** viewer

The command displays DHCP relay statistics.

**Command syntax:show interfaces dhcp relay statistics** [interface-name]

**Command mode:** operational



**Note**

- The command is applicable to the following interface types:

	- physicals

	- physical vlans

	- bundles

	- bundle vlans

	- IRB


- Specify an interface to filter the displayed information to that interface.

- The displayed counters only count DHCP packets that are relayed. Unicast traffic between the DHCP server and the client is not relayed and thus is not counted.

**Parameter table**

+----------------+-----------------------------------------------------------+----------------------------------------------------+-----------+
| Parameter      | Description                                               | Range                                              | Default   |
+================+===========================================================+====================================================+===========+
| interface-name | Filters the displayed information to a specific interface | geX-X/X/X, geX-X/X/X.Y, bundle-X, bundle-X.Y, irbX | \-        |
+----------------+-----------------------------------------------------------+----------------------------------------------------+-----------+

**Example**
::

	dnRouter# show interfaces dhcp relay statistics

	| Interface           | Admin    | Total RX       | Total TX       | Total Drops      |
	+---------------------+----------+----------------+----------------+------------------+
	| bundle-2            | enabled  | 100            | 105            | 0                |
	| bundle-2.250        | disabled | 0              | 0              | 0                |
	| ge100-0/0/0         | enabled  | 200            | 200            | 0                |
	| ge100-0/0/0.100     | enabled  | 0              | 0              | 0                |
	| irb3                | enabled  | 0              | 0              | 0                |


	dnRouter# show interfaces dhcp relay statistics ge100-0/0/0

	Interface ge100-0/0/0
		DHCPv4 relay:
			Admin state: enabled
			Source address: 1.1.1.1
			Packets dropped:
				Total drops:               0
				Invalid option-82:         0
			Messages received:
				Total RX                   235
				BOOTREQUEST                116
				BOOTREPLY                  0
				DHCPDECLINE                0
				DHCPDISCOVER               11
				DHCPINFORM                 0
				DHCPRELEASE                0
				DHCPREQUEST                105
				DHCPOFFER                  2
				DHCPACK                    1
				DHCPNAK                    0
			Messages sent:
				Total TX                   235
				BOOTREQUEST                116
				BOOTREPLY                  0
				DHCPDECLINE                0
				DHCPDISCOVER               11
				DHCPINFORM                 0
				DHCPRELEASE                0
				DHCPREQUEST                105
				DHCPOFFER                  2
				DHCPACK                    1
				DHCPNAK                    0


.. **Help line:** show dhcp relay statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
