show arp
--------

**Minimum user role:** viewer

The show arp command displays the ARP tables of all interfaces, per VRF. You can filter the display to show the ARP table of a specific interface by specifying the interface-name, or ipv4-address and/or of a specific VRF.

**Command syntax: show arp** {vrf [vrf-name] | all} \| interface [interface-name] \| ipv4-address [ipv4-address]

**Command mode:** operational


..
	**Internal Note**

	-  When a user selects a specific interface/ipv4-address it will filter according to it

	-  When vrf name not specified, default vrf will be shown as default

	-  When user selects management interface, NO ARP entries will be presented this data is preserved under the vrf-name mgmt0, mgmt-ncc-0 and mgmt-ncc-1.

	-  only one of mgmt-ncc-0 and mgmt-ncc-1 will show the ARP entries and it is the active NCC.

	-  mgmt-ncc-0 and mgmt-ncc-1 are under VRFs mgmt-ncc-0 and mgmt-ncc-1 correspondingly mgmt0 is under VRF mgmt0

	-  Age column displays a dynamic ARP entry's age

	-  Entries of local origin are not valid ARP entries, but merely list an interface's local IPv4 and MAC addresses for convenience.

**Parameter table**

+----------------+----------------------------------------------------------------+----------------------------+-----------------+
| Parameter      | Description                                                    | Range                      | Default value   |
+================+================================================================+============================+=================+
| vrf-name       | Filter the ARP entries according to the specified VRF          | An existing VRF name       | /-              |
+----------------+----------------------------------------------------------------+----------------------------+-----------------+
| interface-name | Filter the ARP entries according to the specified interface    | An existing interface name | /-              |
+----------------+----------------------------------------------------------------+----------------------------+-----------------+
| ipv4-address   | Filter the ARP entries according to the specified IPv4 address | A.B.C.D                    | /-              |
+----------------+----------------------------------------------------------------+----------------------------+-----------------+

The following information is displayed:

+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter    | Description                                                                                                                                                                                                     | Options                                                                                                                                                                                                                                                 |
+==============+=================================================================================================================================================================================================================+=========================================================================================================================================================================================================================================================+
| VRF          | The VRF name. The ARP entries are displayed per VRF.                                                                                                                                                            | String                                                                                                                                                                                                                                                  |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| IPv4 Address | The IPv4 address for the ARP entry                                                                                                                                                                              | A.B.C.D                                                                                                                                                                                                                                                 |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MAC Address  | The MAC address corresponding to the IPv4 address                                                                                                                                                               | xx:xx:xx:xx:xx:xx                                                                                                                                                                                                                                       |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|              |                                                                                                                                                                                                                 | Static - the entry was added manually                                                                                                                                                                                                                   |
| Origin       | Displays how the ARP entry was acquired.                                                                                                                                                                        | Dynamic - see Dynamic ARP                                                                                                                                                                                                                               |
|              |                                                                                                                                                                                                                 | Local - shows an interface's local IPv4 and MAC addresses for convenience (not a valid ARP entry).                                                                                                                                                      |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| State        | Indicates the state of the ARP cache entry:                                                                                                                                                                     | Static - the entry was manually added to the ARP table (see interfaces arp); static entries do not age out.                                                                                                                                             |
|              | All states except "static", are for dynamically learned entries.                                                                                                                                                | Incomplete - an ARP request was sent but the MAC address is still unknown.                                                                                                                                                                              |
|              |                                                                                                                                                                                                                 | Reachable - normal entry expiration                                                                                                                                                                                                                     |
|              |                                                                                                                                                                                                                 | Stale - the ARP entry has expired but needs verification (it is still usable)                                                                                                                                                                           |
|              |                                                                                                                                                                                                                 | Delay - schedule an ARP request                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 | Probe - sending an ARP request                                                                                                                                                                                                                          |
|              |                                                                                                                                                                                                                 | Failed - entries for which ARP requests were sent, but ARP replies were not received. ARP entries from “INCOMPLETE” and “DELAY” state can become “FAILED” if no ARP replies were received.                                                              |
|              |                                                                                                                                                                                                                 | Noarp - ARP requests are never sent to verify expired ARP entries. If an interface is set to “NOARP” mode, all the ARP entries in “REACHABLE” state become “NOARP” after ARP stale timeout. DNOS does not provide “NOARP” interface mode configuration. |
|              |                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                         |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Age          | The amount of time that the entry exists in the ARP table. The age is displayed for dynamic entries only.                                                                                                       | days, HH:MM:SS                                                                                                                                                                                                                                          |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Interface    | The name of the interface from which the entry was learned. For static entries, this is the interface on which the entry was configured. The ARP entry will be distributed to the interface's broadcast domain. | ge<interface speed>-<A>/<B>/<C>                                                                                                                                                                                                                         |
|              | When selecting the mgmt0 interface, the ARP entries are displayed for mgmt-ncc-0 or mgmt-ncc-1, depending on which is the currently active NCC.                                                                 |                                                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>                                                                                                                                                                                                      |
|              |                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 | bundle-<bundle id>                                                                                                                                                                                                                                      |
|              |                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 | bundle-<bundle id>.<sub-interface id>                                                                                                                                                                                                                   |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show arp

	VRF: default
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	|--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.2     | 7c:fe:90:57:73:81 | static  | static         |                  | ge100-1/8/1  |
	| 30.1.1.3     | 7c:fe:90:57:73:82 | dynamic | stale          | 0 days, 00:00:01 | ge100-1/8/1  |
	| 30.1.1.8     | 84:40:76:cc:b8:b9 | local   |                |                  | ge100-1/8/1  |
	| 40.1.1.2     | 7c:fe:90:57:73:83 | dynamic | reachable      | 0 days, 00:02:14 | ge100-3/8/1  |
	| 40.1.1.8     | e8:c4:5d:08:6a:13 | local   |                |                  | ge100-3/8/1  |

	dnRouter# show arp interface ge100-1/8/1

	VRF: default
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	|--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.2     | 7c:fe:90:57:73:81 | static  | static         |                  | ge100-1/8/1  |
	| 30.1.1.3     | 7c:fe:90:57:73:82 | dynamic | stale          | 0 days, 00:00:43 | ge100-1/8/1  |
	| 30.1.1.8     | 84:40:76:cc:b8:b9 | local   |                |                  | ge100-1/8/1  |

	dnRouter# show arp ipv4-address 30.1.1.2

	VRF: default
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	|--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.2     | 7c:fe:90:57:73:81 | static  | static         |                  | ge100-1/8/1  |

	dnRouter# show arp vrf my_vrf ipv4-address 30.1.1.3

	VRF: my_vrf
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	|--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.3     | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | ge100-0/0/12 |

	dnRouter# show arp vrf mgmt0

	VRF: mgmt0
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	+--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.2     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt0        |
	| 30.1.1.3     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt0        |

	dnRouter# show arp vrf mgmt-ncc-0

	VRF: mgmt-ncc-0
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	+--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.4     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |
	| 30.1.1.5     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |

	dnRouter# show arp vrf all

	VRF: default
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	|--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.2     | 7c:fe:90:57:73:81 | static  | static         |                  | ge100-1/8/1  |
	| 30.1.1.3     | 7c:fe:90:57:73:82 | dynamic | stale          | 0 days, 00:00:01 | ge100-1/8/1  |
	| 30.1.1.8     | 84:40:76:cc:b8:b9 | local   |                |                  | ge100-1/8/1  |
	| 40.1.1.2     | 7c:fe:90:57:73:83 | dynamic | reachable      | 0 days, 00:02:14 | ge100-3/8/1  |
	| 40.1.1.8     | e8:c4:5d:08:6a:13 | local   |                |                  | ge100-3/8/1  |

	VRF: my_vrf
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	|--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.3     | 7c:fe:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | ge100-0/0/12 |

	VRF: mgmt0
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	+--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.2     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt0        |
	| 30.1.1.3     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt0        |

	VRF: mgmt-ncc-0
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	+--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.4     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |
	| 30.1.1.5     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |

	VRF: mgmt-ncc-1
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	+--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.4     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |
	| 30.1.1.5     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |


.. **Help line:** show arp information

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 5.1.0   | Command introduced                                      |
+---------+---------------------------------------------------------+
| 10.0    | Added support for mgmt0 and mgmt-ncc                    |
+---------+---------------------------------------------------------+
| 11.0    | Added "Failed" and "Noarp" states.                      |
+---------+---------------------------------------------------------+
| 13.3    | Added ARP entries' origin and age                       |
+---------+---------------------------------------------------------+
| 16.1    | Added support to display entries from a specific VRF    |
+---------+---------------------------------------------------------+