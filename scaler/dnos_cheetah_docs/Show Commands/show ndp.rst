show ndp
--------

**Minimum user role:** viewer

The show ndp command displays the NDP tables of all interfaces, per VRF. You can filter the display to show the NDP table of a specific interface by specifying the interface-name or ipv6-address, and/or of a specific VRF.

**Command syntax: show ndp** {vrf [vrf-name] | all} \| interface [interface-name] \| ipv6-address [ipv6-address]

**Command mode:** operational


..
	**Internal Note**

	- [vrf-name] | [interface-name] | [ipv6-address]: filter the NDP entries according to a specific VRF, an interface-name, or a specific IPv6-address.

	-  When a user selects a specific interface/ipv6-address it will filter according to it

	- When vrf name not specified, default vrf will be shown as default

	- When user selects management interface, NO ARP entries will be presented this data is preserved under the vrf-name mgmt0, mgmt-ncc-0 and mgmt-ncc-1.

	- only one of mgmt-ncc-0 and mgmt-ncc-1 will show the ARP entries and it is the active NCC.

	- mgmt-ncc-0 and mgmt-ncc-1 are under VRFs mgmt-ncc-0 and mgmt-ncc-1 correspondingly mgmt0 is under VRF mgmt0

	- Age column displays a dynamic NDP entry's age

**Parameter table**

The following information is displayed:

+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter    | Description                                                                                                                                                                                                     | Options                                                                                                                                                                                                                                                 |
+==============+=================================================================================================================================================================================================================+=========================================================================================================================================================================================================================================================+
| VRF          | The VRF name. The ARP entries are displayed per VRF.                                                                                                                                                            | String: default, mgmt0, mgmt-ncc-0, mgmt-ncc-1, etc | all                                                                                                                                                                                               |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| IPv6 Address | The IPv6 address for the NDP entry                                                                                                                                                                              | x:x::x:x                                                                                                                                                                                                                                                |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MAC Address  | The MAC address corresponding to the IPv4 address                                                                                                                                                               | xx:xx:xx:xx:xx:xx                                                                                                                                                                                                                                       |
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
| Interface    | The name of the interface from which the entry was learned. For static entries, this is the interface on which the entry was configured. The NDP entry will be distributed to the interface's broadcast domain. | This command is applicable to the following interfaces:                                                                                                                                                                                                 |
|              | When selecting the mgmt0 interface, the NDP entries are displayed for mgmt-ncc-0 or mgmt-ncc-1, depending on which is the currently active NCC.                                                                 |                                                                                                                                                                                                                                                         |
|              | mgmt0, mgmt-ncc-0 and mgmt-ncc-1 are not related to any VRF.                                                                                                                                                    | ge<interface speed>-<A>/<B>/<C>                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>                                                                                                                                                                                                      |
|              |                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 | bundle-<bundle id>                                                                                                                                                                                                                                      |
|              |                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 | bundle-<bundle id>.<sub-interface id>                                                                                                                                                                                                                   |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Type         | The neighbor type                                                                                                                                                                                               | router                                                                                                                                                                                                                                                  |
|              |                                                                                                                                                                                                                 | host                                                                                                                                                                                                                                                    |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show ndp

	VRF: default
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:23  | ge100-1/8/1  | Router    |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 01:06:22  | ge100-1/8/1  | Router    |
	| 2001:1234::1      | 7c:fe:90:57:73:83 | dynamic | reachable      | 0 days, 04:01:07  | ge100-3/8/1  | Host      |

	dnRouter# show ndp interface ge100-1/8/1

	VRF: default
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:01:23  | ge100-1/8/1  | Router    |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 01:07:22  | ge100-1/8/1  | Router    |

	dnRouter# show ndp ipv6-address 2001:1234::1

	VRF: default
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:01:49  | ge100-1/8/1  | Router    |

	dnRouter# show ndp vrf my_vrf ipv6-address 2001:1234::2

	VRF: my_vrf
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::2      | 7c:fe:90:57:73:83 | dynamic | reachable      | 0 days, 04:08:12  | ge100-3/8/1  | Host      |

	dnRouter# show ndp vrf mgmt-ncc-0

	VRF: mgmt-ncc-0
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:24  | mgmt-ncc-0   | Host      |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:02:48  | mgmt-ncc-0   | Host      |

	dnRouter# show ndp vrf mgmt0

	VRF: mgmt0
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:49  | mgmt0        | Host      |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:03:13  | mgmt0        | Host      |

	dnRouter# show ndp vrf all

	VRF: default
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:23  | ge100-1/8/1  | Router    |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 01:06:22  | ge100-1/8/1  | Router    |
	| 2001:1234::1      | 7c:fe:90:57:73:83 | dynamic | reachable      | 0 days, 04:01:07  | ge100-3/8/1  | Host      |

	VRF: my_vrf
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::2      | 7c:fe:90:57:73:83 | dynamic | reachable      | 0 days, 04:08:12  | ge100-3/8/1  | Host      |

	VRF: mgmt0
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:49  | mgmt0        | Host      |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:03:13  | mgmt0        | Host      |

	VRF: mgmt-ncc-0
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:24  | mgmt-ncc-0   | Host      |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:02:48  | mgmt-ncc-0   | Host      |

	VRF: mgmt-ncc-1
	| IPv6 Address      | MAC Address       | Origin  | State          | Age               | Interface    | Type      |
	|-------------------+-------------------+---------+----------------+-------------------+--------------+-----------|
	| 2001:1234::1      | 7c:fe:90:57:73:81 | dynamic | reachable      | 0 days, 00:00:24  | mgmt-ncc-1   | Host      |
	| 2001:1234:3333::1 | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:02:48  | mgmt-ncc-1   | Host      |


.. **Help line:** show ndp information

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 5.1.0   | Command introduced                   |
+---------+--------------------------------------+
| 10.0    | Added support for mgmt0 and mgmt-ncc |
+---------+--------------------------------------+
| 11.0    | Added "Failed" and "Noarp" states    |
+---------+--------------------------------------+
| 13.3    | Added NDP entries' origin and age    |
+---------+--------------------------------------+
| 16.1    | Added the all option to the VRF      |
+---------+--------------------------------------+
