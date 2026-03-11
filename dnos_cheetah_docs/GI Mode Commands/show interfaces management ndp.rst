show ndp
------------------------------

**Minimum user role:** viewer

The command displays the NDP tables of management interfaces. To filter the display to show the NDP table of a specific interface by specifying the interface-name and/or ipv6-address:

**Command syntax: show ndp** {interface [interface-name] \| ipv6-address [ipv6-address]

**Command mode:** operational


..
	**Internal Note**

	- [interface-name] | [ipv6-address]: filter the NDP entries according to a specific interface-name, and/or a specific IPv6-address.

	-  When a user selects a specific interface/ipv6-address it will filter according to it

	- Age column displays a dynamic NDP entry's age

**Parameter table**

The following information is displayed:

+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter    | Description                                                                                                                                                                                                     | Options                                                                                                                                                                                                                                                 |
+==============+=================================================================================================================================================================================================================+=========================================================================================================================================================================================================================================================+
| IPv6 Address | The IPv6 address for the NDP entry                                                                                                                                                                              | x:x::x:x                                                                                                                                                                                                                                                |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MAC Address  | The MAC address corresponding to the IPv6 address                                                                                                                                                               | xx:xx:xx:xx:xx:xx                                                                                                                                                                                                                                       |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Origin       | Displays how the NDP entry was acquired                                                                                                                                                                         | Static - the entry was added manually                                                                                                                                                                                                                   |
|              |                                                                                                                                                                                                                 | Dynamic - see Dynamic ARP                                                                                                                                                                                                                               |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| State        | Indicates the state of the NDP cache entry.                                                                                                                                                                     | Static - the entry was manually added to the NDP table (see interfaces ndp)                                                                                                                                                                             |
|              | All states except "static", are for dynamically learned entries.                                                                                                                                                | Incomplete - an NDP request was sent but the MAC address is still unknown.                                                                                                                                                                              |
|              |                                                                                                                                                                                                                 | Reachable - normal entry expiration                                                                                                                                                                                                                     |
|              |                                                                                                                                                                                                                 | Stale - the entry has expired but needs verification (it is still usable)                                                                                                                                                                               |
|              |                                                                                                                                                                                                                 | Delay - schedule an NDP request                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 | Probe - sending an NDP request                                                                                                                                                                                                                          |
|              |                                                                                                                                                                                                                 | Failed - entries for which NDP requests were sent, but NDP replies were not received. NDP entries from “INCOMPLETE” and “DELAY” state can become “FAILED” if no NDP replies were received.                                                              |
|              |                                                                                                                                                                                                                 | Noarp - NDP requests are never sent to verify expired NDP entries. If an interface is set to “NOARP” mode, all the NDP entries in “REACHABLE” state become “NOARP” after the stale timeout. DNOS does not provide “NOARP” interface mode configuration. |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Age          | The amount of time that the entry exists in the NDP table. The age is displayed for dynamic entries only.                                                                                                       | days, HH:MM:SS                                                                                                                                                                                                                                          |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Interface    | The name of the interface from which the entry was learned. The NDP entry will be distributed to the interface's broadcast domain.                                                                              | This command is applicable to the following interfaces:                                                                                                                                                                                                 |
|              | When selecting the interface mgmt-ncc-0 or mgmt-ncc-1, the NDP entries are displayed for only mgmt-ncc-0 or mgmt-ncc-1 correspondingly.                                                                         | mgmt-ncc-0, mgmt-ncc-1                                                                                                                                                                                                                                  |
|              |                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                         |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Type         | The neighbor type                                                                                                                                                                                               | router                                                                                                                                                                                                                                                  |
|              |                                                                                                                                                                                                                 | host                                                                                                                                                                                                                                                    |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show ndp

	Interface: mgmt-ncc-0
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:24  | mgmt-ncc-0   | Host      |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:02:48  | mgmt-ncc-0   | Host      |

	Interface: mgmt-ncc-1
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:24  | mgmt-ncc-1   | Host      |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:02:48  | mgmt-ncc-1   | Host      |

	dnRouter# show ndp interface mgmt-ncc-0
	
	Interface: mgmt-ncc-0
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:24  | mgmt-ncc-0   | Host      |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:02:48  | mgmt-ncc-0   | Host      |

.. **Help line:** show ndp information

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 16.2    | Command introduced                                      |
+---------+---------------------------------------------------------+
