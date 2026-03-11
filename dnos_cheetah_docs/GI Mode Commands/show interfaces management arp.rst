show arp
------------------------------

**Minimum user role:** viewer

The command displays the ARP tables of management interfaces. To filter the display to show the ARP table of a specific interface by specifying the interface-name and/or ipv4-address:

**Command syntax: show arp** {interface [interface-name] \| ipv4-address [ipv4-address]

**Command mode:** operational


..
	**Internal Note**

	-  When a user selects a specific interface/ipv4-address it will filter according to it

	-  Age column displays a dynamic ARP entry's age

	-  Entries of local origin are not valid ARP entries, but merely list an interface's local IPv4 and MAC addresses for convenience.

**Parameter table**

+----------------+----------------------------------------------------------------+----------------------------+-----------------+
| Parameter      | Description                                                    | Range                      | Default value   |
+================+================================================================+============================+=================+
| interface-name | Filter the ARP entries according to the specified interface    | An existing interface name | /-              |
+----------------+----------------------------------------------------------------+----------------------------+-----------------+
| ipv4-address   | Filter the ARP entries according to the specified IPv4 address | A.B.C.D                    | /-              |
+----------------+----------------------------------------------------------------+----------------------------+-----------------+

The following information is displayed:

+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter    | Description                                                                                                                                                                                                     | Options                                                                                                                                                                                                                                                 |
+==============+=================================================================================================================================================================================================================+=========================================================================================================================================================================================================================================================+
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
| Interface    | The name of the interface from which the entry was learned.                                                                                                                                                     | mgmt-ncc-x                                                                                                                                                                                                                                              |
|              | When selecting the interface mgmt-ncc-0 or mgmt-ncc-1, the NDP entries are displayed for only mgmt-ncc-0 or mgmt-ncc-1 correspondingly.                                                                         |                                                                                                                                                                                                                                                         |
|              |                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                         |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show arp

	Interface: mgmt-ncc-0
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	+--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.4     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |
	| 30.1.1.5     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |

	Interface: mgmt-ncc-1
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	+--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.4     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |
	| 30.1.1.5     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |

	dnRouter# show arp interface mgmt-ncc-0

	VRF: mgmt-ncc-0
	| IPv4 Address | MAC Address       | Origin  | State          | Age              | Interface    |
	+--------------+-------------------+---------+----------------+------------------+--------------|
	| 30.1.1.4     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |
	| 30.1.1.5     | 7c:ae:90:57:73:82 | dynamic | reachable      | 0 days, 00:00:04 | mgmt-ncc-0   |

.. **Help line:** show arp information

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 17.1    | Command introduced                                      |
+---------+---------------------------------------------------------+
