show vrrp
---------

**Minimum user role:** viewer

The show vrrp command displays concentric information of all VRRP enabled interfaces, or a subset thereof according to the filters. If an interface name is specified, then a detailed output for the requested interface is displayed.

**Command syntax: show vrrp** vrf [vrf-name] interface [interface-name] address-family [address-family] state [protocol-state] vrid [vrrp-id]

**Command mode:** operational

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle

	- Bundle vlan

	- IRB

- When a user selects a specific interface, it will filter the output according to it.

- By default the output is shown for default VRF. To display the output for VRRP interfaces on another VRF instance the vrf filter should be used. Several filters may be applied at the same time.


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
| Protocol State             | The state of the VRRP protocol for the group on the interface.                                                         | Init Backup Master | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Priority                   | The current priority of the router for the VRRP group on the interface.                                                | 0..255             | 100       |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Address Family             | The address family of the VRRP group on the interface.                                                                 | IPv4 IPv6          | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Virtual MAC Address        | The virtual MAC address assigned for the VRRP router.                                                                  | xx:xx:xx:xx:xx:xx  | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+
| Virtual IP Address(es)     | The virtual IP addresses associated with the VRRP group.                                                               | A.B.C.D x:x::x:x   | \-        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------+--------------------+-----------+

The following information is displayed for each named interface:

+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Field                    | Description                                                                                                                                   | Options            | Default  |
+==========================+===============================================================================================================================================+====================+==========+
| Interface                | The name of the interface.                                                                                                                    | String             | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Admin                    | The administrative status, indicates whether or not VRRP is currently enabled on the interface is currently enabled.                          | Enabled Disabled   | Enabled  |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| VRF                      | The VRF instance that the interface is associated with.                                                                                       | String             | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| VRRP Version             | The version of the VRRP protocol.                                                                                                             | 3                  | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| VRID                     | The virtual router identifier of the VRRP group.                                                                                              | 1-255              | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Description              | The description of the VRRP group.                                                                                                            | String             | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Protocol State           | The state of the VRRP protocol for the group on the interface.                                                                                | Init Backup Master | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Priority                 | The current priority of the router for the VRRP group on the interface.                                                                       | 0-255              | 100      |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Address Family           | The address family of the VRRP group on the interface.                                                                                        | IPv4 IPv6          | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| CoS                      | The class of service that shall be set for outgoing VRRPv3 control packets.                                                                   | 0..56              | 48       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Virtual MAC Address      | The virtual MAC address assigned for the VRRP router.                                                                                         | xx:xx:xx:xx:xx:xx  | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Virtual IP Address(es)   | The virtual IP addresses associated with the VRRP group.                                                                                      | A.B.C.D x:x::x:x   | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Number of state changes  | The number of VRRP protocol state transitions for the VRRP group.                                                                             | Integer            | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Last state change        | The time since the last state transition occured for the VRRP group. The time resets to zero when the interface is down.                      | D days, HH:MM:SS   | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Last state change reason | The reason for the last state change of the VRRP protocol for the group.                                                                      | String             | \-       |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Preempt Mode             | When activated enables preemption by a higher priority backup router of a lower priority master router.                                       | Enabled Disabled   | Enabled  |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Preempt Delay            | The delay in seconds that the higher priority router waits before preempting.                                                                 | 0..3600            | 1        |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Startup Delay            | The delay in seconds that the higher priority backup router waits before preempting the master router after an interface becomes operational. | 0..3600            | 300      |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Accept Mode              | Dicatates whether packets destined for virtual addresses are accepted even when the virtual address is not owned by the router interface.     | Enabled Disabled   | Disabled |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+
| Advertisement Time       | The interval in seconds between successive VRRP advertisements.                                                                               | 100..65535         | 1000     |
+--------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------+--------------------+----------+


**Example**
::

	dnRouter# show vrrp

	Legend: m - multiple IP addresses

	VRF: default
	| Interface   	 | Admin    | VRID  | Address Family | Protocol State  | Priority | Virtual MAC Address | Virtual IP Address |
	+----------------+----------+-------+----------------+-----------------+----------+---------------------+--------------------+
	| bundle-2       | enabled  | 1     | IPv4           | Master (owner)  | 255      | 00:00:5e:00:01:01   | 4.4.4.4            |
	| bundle-2       | enabled  | 4     | IPv6           | Master          | 215      | 00:00:5e:00:02:04   | 1004:abcd:12::2    |
	| bundle-3.100   | disabled | 4     | IPv6           | Init            | 100      | 00:00:5e:00:02:04   | 2001:608::         |
	| ge100-1/0/1 	 | enabled  | 7     | IPv4           | Backup          | 240      | 00:00:5e:00:01:07   | 10.10.10.10 (m)    |

	Total displayed virtual routers: 4


	dnRouter# show vrrp address-family ipv4

	Legend: m - multiple IP addresses

	VRF: default
	| Interface   	 | Admin    | VRID  | Address Family | Protocol State  | Priority | Virtual MAC Address | Virtual IP Address |
	+----------------+----------+-------+----------------+-----------------+----------+---------------------+--------------------+
	| bundle-2       | enabled  | 1     | IPv4           | Master (owner)  | 255      | 00:00:5e:00:01:01   | 4.4.4.4            |
	| ge100-1/0/1 	 | enabled  | 7     | IPv4           | Backup          | 240      | 00:00:5e:00:01:07   | 10.10.10.10 (m)    |

	Total displayed virtual routers: 2


	dnRouter# show vrrp state master

	Legend: m - multiple IP addresses

	| Interface   	 | Admin    | VRID  | Address Family | Protocol State  | Priority | Virtual MAC Address | Virtual IP Address |
	+----------------+----------+-------+----------------+-----------------+----------+---------------------+--------------------+
	| bundle-2       | enabled  | 1     | IPv4           | Master (owner)  | 255      | 00:00:5e:00:01:01   | 4.4.4.4            |
	| bundle-2       | enabled  | 4     | IPv6           | Master          | 215      | 00:00:5e:00:02:04   | 1004:abcd:12::2    |

	Total displayed virtual routers: 2


	dnRouter# show vrrp vrid 4

	Legend: m - multiple IP addresses

	| Interface   	 | Admin    | VRID  | Address Family | Protocol State  | Priority | Virtual MAC Address | Virtual IP Address |
	+----------------+----------+-------+----------------+-----------------+----------+---------------------+--------------------+
	| bundle-2       | enabled  | 4     | IPv6           | Master          | 215      | 00:00:5e:00:02:04   | 1004:abcd:12::2    |

	Total displayed virtual routers: 2


	dnRouter# show vrrp vrf MyVRF-1

	Legend: m - multiple IP addresses

	VRF: MyVRF-1
	| Interface   	  | Admin    | VRID  | Address Family | Protocol State  | Priority | Virtual MAC Address | Virtual IP Address |
	+-----------------+----------+-------+----------------+-----------------+----------+---------------------+--------------------+
	| ge400-0/0/0.100 | enabled  | 2     | IPv4           | Master          | 230      | 00:00:5e:00:01:02   | 4.4.4.4            |

	Total displayed virtual routers: 1


	dnRouter# show vrrp interface ge100-1/0/1

	Interface ge100-1/0/1
	  VRRP version: 3, VRID: 7, Address Family: IPv4, CoS: 48
	  Description:
	  Admin state: enabled, Protocol state: Backup
	  Number of state changes: 6, Last state change: 0 days, 00:00:01
	  Master router is unknown
	  Last state change reason: Master router is IP address owner (10.10.10.10)
	  Virtual MAC Address: 00:00:5e:00:01:07
	  Virtual IPv6 Link Local Address: N/A
	  Virtual IP address(es):
	    10.10.10.10
		10.10.10.20
		10.10.10.30 (local)
	  Configured priority: 240, Current priority: 215
	  Preempt mode: enabled, Preempt delay: 2 seconds, Startup delay: 300 seconds
	  Accept mode: disabled
	  Advertisement time: 1 seconds
	  Master down timer: 3.160
	  Tracked objects: 1/2 up, priority decrement 25
		| Type       | Object                   | State  | Priority Decrement |
		+------------+--------------------------+--------+--------------------+
		| interface  | ge100-0/0/0.200          | down   | 25                 |
		| route      | 192.168.1.100/24:default | up     | 100                |


.. **Help line:** show vrrp

**Command History**

+---------+------------------------------------------------+
| Release | Modification                                   |
+=========+================================================+
| 17.2    | Command introduced                             |
+---------+------------------------------------------------+
| 18.2    | Added global parameters to the detailed output |
+---------+------------------------------------------------+
