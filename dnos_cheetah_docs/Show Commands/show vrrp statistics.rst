show vrrp statistics
--------------------

**Minimum user role:** viewer

The show vrrp statistics command displays global and per interface statistics of VRRP enabled interfaces.

**Command syntax: show vrrp statistics** vrf [vrf-name] interface [interface-name] address-family [address-family] state [protocol-state] vrid [vrrp-id]

**Command mode:** operational

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle

	- Bundle vlan

	- When a user selects a specific interface, it will filter the output according to it.


**Parameter table**

+----------------+------------------------------------------------------------------------+----------------------------------------------+---------+
| Parameter      | Description                                                            | Range                                        | Default |
+================+========================================================================+==============================================+=========+
| interface-name | Filters the displayed information to the specified interface           | geX-X/X/X, geX-X/X/X.Y, bundle-X, bundle-X.Y | \-      |
+----------------+-----------------------------------------------------------------------------------------------------------------------+---------+
| vrf-name       | Filters the displayed information to the specified VRF instance        | String                                       | \-      |
+----------------+------------------------------------------------------------------------+----------------------------------------------+---------+
| address-family | Filters the displayed information to the specified address family      | IPv4 IPv6                                    | \-      |
+----------------+-----------------------------------------------------------------------------------------------------------------------+---------+
| state          | Filters the displayed information to the specified VRRP protocol state | Init Backup Master                           | \-      |
+----------------+-----------------------------------------------------------------------------------------------------------------------+---------+
| vrid           | Filters the displayed information to the specified VRRP ID             | Integer                                      | \-      |
+----------------+-----------------------------------------------------------------------------------------------------------------------+---------+

The following information is displayed for each interface in the concentrated table:

+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Field                      | Description                                                                                                            | Range              | Default   |
+============================+========================================================================================================================+====================+===========+
| Interface                  | The name of the interface.                                                                                             | String             | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Admin                      | The administrative status, indicates whether or not VRRP is currently enabled on the interface is currently enabled.   | Enabled Disabled   | Enabled   |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| VRID                       | The virtual router identifier of the VRRP group.                                                                       | 1..255             | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Address Family             | The address family of the VRRP group on the interface.                                                                 | IPv4 IPv6          | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Protocol State             | The state of the VRRP protocol for the group on the interface.                                                         | Init Backup Master | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| RX Announcements           | The total number of VRRP announcements received on the interface for AFI-VRID.                                         | Integer            | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| TX Announcements           | The total number of VRRP announcements transmitted on the interface for AFI-VRID.                                      | Integer            | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Total Drops                | The total number of VRRP announcements discarded on the interface for AFI-VRID.                                        | Integer            | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+


The following information is displayed for each named interface:

+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Field                      | Description                                                                                                                                   | Options            | Default   |
+============================+===============================================================================================================================================+====================+===========+
| Interface                  | The name of the interface.                                                                                                                    | String             | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Admin                      | The administrative status, indicates whether or not VRRP is currently enabled on the interface is currently enabled.                          | Enabled Disabled   | Enabled   |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| VRRP Version               | The version of the VRRP protocol.                                                                                                             | 3                  | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| VRID                       | The virtual router identifier of the VRRP group.                                                                                              | 1..255             | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Description                | The description of the VRRP group.                                                                                                            | String             | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Protocol State             | The state of the VRRP protocol for the group on the interface.                                                                                | Init Backup Master | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Priority                   | The current priority of the router for the VRRP group on the interface.                                                                       | 0..255             | 100       |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Address Family             | The address family of the VRRP group on the interface.                                                                                        | IPv4 IPv6          | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Virtual MAC Address        | The virtual MAC address assigned for the VRRP router.                                                                                         | xx:xx:xx:xx:xx:xx  | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Virtual IP Address(es)     | The virtual IP addresses associated with the VRRP group.                                                                                      | A.B.C.D x:x::x:x   | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Number of state changes    | The number of VRRP protocol state transitions for the VRRP group.                                                                             | Integer            | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Last state change          | The time since the last state transition occured for the VRRP group. The time resets to zero when the interface is down.                      | D days, HH:MM:SS   | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Last state change reason   | The reason for the last state change of the VRRP protocol for the group.                                                                      | String             | \-        |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Preempt Mode               | When activated enables preemption by a higher priority backup router of a lower priority master router.                                       | Enabled Disabled   | Enabled   |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Preempt Delay              | The delay in seconds that the higher priority router waits before preempting.                                                                 | 1..3600            | 1         |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Accept Mode                | Dicatates whether packets destined for virtual addresses are accepted even when the virtual address is not owned by the router interface.     | Enabled Disabled   | Disabled  |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Advertisement Time         | The interval in seconds between successive VRRP advertisements.                                                                               | 100..65535         | 1000      |
+----------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+


**Example**
::

	dnRouter# show vrrp statistics

	| Interface   	 | Admin    | VRID  | Address Family | Protocol State  | RX Announcements | TX Announcements | Total Drops      |
	+----------------+----------+-------+----------------+-----------------+------------------+------------------+------------------+
	| bundle-2       | enabled  | 1     | IPv4           | Master (owner)  | 1                | 289              | 0                |
	| bundle-2       | enabled  | 4     | IPv6           | Master          | 3                | 105              | 0                |
	| bundle-3.100   | disabled | 4     | IPv6           | Init            | 0                | 0                | 0                |
	| ge100-1/0/1 	 | enabled  | 7     | IPv4           | Backup          | 64               | 0                | 2                |

	Total RX Announcements:              68
	Total TX Announcements:              394
	Total Drops:                         2


	dnRouter# show vrrp statistics address-family ipv4

	| Interface   	 | Admin    | VRID  | Address Family | Protocol State  | RX Announcements | TX Announcements | Total Drops      |
	+----------------+----------+-------+----------------+-----------------+------------------+------------------+------------------+
	| bundle-2       | enabled  | 1     | IPv4           | Master (owner)  | 1                | 289              | 0                |
	| ge100-1/0/1 	 | enabled  | 7     | IPv4           | Backup          | 64               | 0                | 2                |

	Total RX Announcements:              65
	Total TX Announcements:              289
	Total Drops:                         2


	dnRouter# show vrrp statistics interface ge100-1/0/1

	Interface ge100-1/0/1
	  VRRP version: 3, VRID: 7, Address Family: IPv4
	  Admin state: enabled, Protocol state: Backup
	  Number of state changes: 6, Last state change: 0 days, 00:00:01
	  Tracked objects: 2
	  RX announcements:                  64
	  RX priority zero:                  0
	  TX announcements:                  0
	  TX priority zero:                  0
	  Total drops:                       2
	  RX address list errors:            0
	  RX checksum errors:                0
	  RX interval errors:                0
	  RX invalid type errors:            0
	  RX packet length errors:           0
	  RX IP TTL errors:                  0
	  RX version errors:                 0
	  RX VRID errors:                    0


.. **Help line:** show vrrp statistics

**Command History**

+---------+------------------------------+
| Release | Modification                 |
+=========+==============================+
| 17.2    | Command introduced           |
+---------+------------------------------+
