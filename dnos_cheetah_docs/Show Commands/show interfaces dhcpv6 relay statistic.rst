show interfaces dhcpv6 relay statistics
---------------------------------------

**Minimum user role:** viewer

The command displays DHCPv6 relay statistics.

**Command syntax:show interfaces dhcpv6 relay statistics** [interface-name]

**Command mode:** operational



**Note**

- The command is applicable to the following interface types:

	- physical

	- physical vlan

	- bundle

	- bundle vlan

- Specify an interface to filter the displayed information.

- The displayed counters only count DHCPv6 packets that are relayed. Unicast traffic between the DHCPv6 server and the client is not relayed and not counted.

**Parameter table**

+----------------+-----------------------------------------------------------+----------------------------------------------------+-----------+
| Parameter      | Description                                               | Range                                              | Default   |
+================+===========================================================+====================================================+===========+
| interface-name | Filters the displayed information to a specific interface | geX-X/X/X, geX-X/X/X.Y, bundle-X, bundle-X.Y       | \-        |
+----------------+-----------------------------------------------------------+----------------------------------------------------+-----------+

**Example**
::

	dnRouter# show interfaces dhcpv6 relay statistics

	| Interface           | Admin    | Total RX       | Total TX       | Total Drops      |
	+---------------------+----------+----------------+----------------+------------------+
	| ge100-0/0/0         | enabled  | 200            | 200            | 0                |
	| ge100-0/0/1         | enabled  | 13             | 13             | 0                |


	dnRouter# show interfaces dhcpv6 relay statistics ge100-0/0/0

	Interface ge100-0/0/0
			DHCPv6 relay:
					Admin state: enabled
					Source address: 123:254:254::67
					Packets dropped:
					Total drops:               0
					Messages received:
							Total RX                   10
							SOLICIT                    5
							REQUEST                    0
							CONFIRM                    0
							RENEW                      0
							REBIND                     0
							RELEASE                    0
							DECLINE                    0
							INFORMATION_REQUEST        0
							RELAY_FORWARD              0
							RELAY_REPLY                5
					Messages sent:
							Total TX                   5
							SOLICIT                    0
							ADVERTISE                  0
							REQUEST                    0
							CONFIRM                    0
							RENEW                      0
							REBIND                     0
							REPLY                      0
							RELEASE                    0
							DECLINE                    0
							RECONFIGURE                0
							INFORMATION_REQUEST        0
							RELAY_FORWARD              5


.. **Help line:** show dhcpv6 relay statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
