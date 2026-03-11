show interfaces management
--------------------------

**Minimum user role:** viewer

To display a list of the management interfaces:

**Command syntax: show interfaces management** [interface-name]

**Command mode:** operational

**Note**

- The command is applicable to the following interface types:

	- console

	- mgmt

	- ipmi


- If the node is not yet configured or is not connected to the NCC, the operational state of its interfaces will display as "not-exist".

- The operational state relates to the link-state (laser state). The uptime for management interfaces is with a "watch" interval of 1 second and is displayed for interfaces with an operational state "up", otherwise the uptime is "0".

- For console interfaces, the serial interface parameters are displayed.

**Parameter table**

+----------------+----------------------------------------------------------------------+-----------------+---------+
| Parameter      | Description                                                          | Range           | Default |
+================+======================================================================+=================+=========+
| interface-name | Optionally filter the displayed information to a specific interface. | mgmt0           | \-      |
|                |                                                                      | mgmt-ncp-x/y    |         |
|                |                                                                      | mgmt-ncf-x/y    |         |
|                |                                                                      | mgmt-ncc-x      |         |
|                |                                                                      | mgmt-ncc-x/y    |         |
|                |                                                                      | ipmi-ncp-x/y    |         |
|                |                                                                      | ipmi-ncf-x/y    |         |
|                |                                                                      | ipmi-ncc-x/y    |         |
|                |                                                                      | console-ncp-x/y |         |
|                |                                                                      | console-ncf-x/y |         |
|                |                                                                      | console-ncc-x/y |         |
+----------------+----------------------------------------------------------------------+-----------------+---------+

The following information is displayed per interface:

+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Field                      | Description                                                                                                                                                                                                                  | Options             | Default |
+============================+==============================================================================================================================================================================================================================+=====================+=========+
| Interface                  | The name of the interface                                                                                                                                                                                                    | String              |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Admin                      | The administrative status, indicates whether or not the interface is currently enabled.                                                                                                                                      | Enabled             |         |
|                            | System-down means that the port was shut down by the system (and not by a user).                                                                                                                                             | Disabled            |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Operational                | The operational state of the interface, indicates whether the link is currently up or down. For physical interfaces, the operational state relates to the link-state (lasar state)                                           | Up                  |         |
|                            | Not-present: the port was pre-provisioned (the NCP is configured but not yet connected to the NCC), or the port was removed due to breakout.                                                                                 | Down                |         |
|                            |                                                                                                                                                                                                                              | Not-present         |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Uptime                     | The amount of time that the interface is up consecutively, with a polling time every 1 second..Uptime relates to physical, Loopback,bundle and subinterface interface types. Uptime resets to zero if the interface is down. | D days, HH:MM:SS    |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Description                | The description provided for the interface.                                                                                                                                                                                  | String              |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| MAC Address                | The MAC Address of the interface. The MAC address is for physical interfaces only.                                                                                                                                           | MAC address format  |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Speed                      | The interface's speed                                                                                                                                                                                                        |                     |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Duplex                     | The directionality of data transmission                                                                                                                                                                                      | Full                |         |
|                            |                                                                                                                                                                                                                              | Half                |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| IPv4 Address               | The configured IPv4 address of the interface. Secondary IPv4 addresses are also listed.                                                                                                                                      | A.B.C.D/x           |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| IPv6 Address               | The configured IPv6 address(es) of the interface. IPv6 addresses are marked as suspended (s) if they are have a 'Tentative' or 'Duplicate' status. (Applicable to IPv6 addresses going through a DAD procedure).             | x:x::x:x/x          |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| ipv6-address-status        | Inaccessible/Unknown/Tentative/Duplicate/Preferred                                                                                                                                                                           |                     |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| ipv6 admin-state           | The administrative state of IPv6 on the interface                                                                                                                                                                            | Enabled             | Enabled |
|                            |                                                                                                                                                                                                                              | Disabled            |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Encapsulation              | The encapsulation that is currently activated on the interface.                                                                                                                                                              | Ethernet            |         |
|                            |                                                                                                                                                                                                                              | 802.1Q              |         |
|                            |                                                                                                                                                                                                                              | QinQ                |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Access-list IPv4/IPv6      | The name of the access list that is applied to the interface.                                                                                                                                                                | String              | \-      |
|                            | "ACL mode disabled" is displayed when the general ACL mode is disabled.                                                                                                                                                      |                     |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| IPv4/IPv6 DHCP             | The administrative status of DHCP on the interface.                                                                                                                                                                          | Enabled             | Enabled |
|                            |                                                                                                                                                                                                                              | Disabled            |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| MTU                        | The configured L2 and L3 maximum transmission unit (MTU), which defines the largest packet size, in bytes, for this interface. L2 MTU default value is 1514, IPv4/IPv6 default values are 1500.                              | Bytes               |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| ARP-timeout                | The configured amount of time (in seconds) that an ARP entry will remain in the ARP cache.                                                                                                                                   | Integer             | 3600    |
|                            |                                                                                                                                                                                                                              | 60..14400 (seconds) |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| NDP-timeout                | The configured amount of time (in seconds) that an NDP entry will remain in the NDP cache.                                                                                                                                   | Integer             | 3600    |
|                            |                                                                                                                                                                                                                              | 60..14400 (seconds) |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| SNMP ifindex               | SNMP Management Information Base (MIB) uses Interface Index (ifIndex) to assign a unique value to each interface.                                                                                                            | Integer             |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| VRF                        | The VRF associated with the interface.                                                                                                                                                                                       | String              |         |
+----------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| Member State               | The operational state of the bundle member.                                                                                                                                                                                  | Up                  | \-      |
|                            |                                                                                                                                                                                                                              | Down                |         |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+
| Reason for last down state | Displays the reason why the physical interface went down                                                                                                                                                                     | string              | \-      |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+---------+

**Example**
::

	
	dnRouter# show interfaces management
	
	| Interface         | Admin    | Operational   | IPv4 Address   | IPv6 Address                   | MTU  | VRF        |
	+-------------------+----------+---------------+----------------+--------------------------------+------|------------|
	| console-ncc-0/0   | enabled  |               |                |                                |      |            |
	| console-ncf-0/0   | enabled  |               |                |                                |      |            |
	| console-ncp-1/0   | disabled |               |                |                                |      |            |
	| ipmi-ncc-0/0      | enabled  |               | 200.1.1.2/24   |                                |      |            |
	| ipmi-ncf-0/0      | enabled  |               | 1.1.1.1/24     |                                |      |            |
	| ipmi-ncp-0/0      | enabled  |               | 1.1.1.2/24     |                                |      |            |
	| ipmi-ncm-A0/0     | enabled  |               | 1.1.1.3/24     |                                |      |            |
	| ipmi-ncm-B0/0     | enabled  |               | 1.1.1.4/24     |                                |      |            |
	| mgmt0             | enabled  | up            | 10.1.1.20/32   | 2010::0001:0001:0001:0020/128  | 1514 | mgmt0      |
	| mgmt-ncc-0        |          | not-exist     | 200.1.1.3/32   | 1006:abcd:12::1/128            | 1514 | mgmt-ncc-0 |
	| mgmt-ncc-1        | enabled  | up            | 200.1.1.4/32   | 1006:abcd:12::2/128            | 1514 | mgmt-ncc-1 |
	| mgmt-ncc-1/0      | enabled  | up            |                |                                |      | mgmt-ncc-1 |
	| mgmt-ncc-1/0      | enabled  | up            |                |                                |      | mgmt-ncc-1 |
	
	
	dnRouter# show interfaces mgmt0

	Interface mgmt0
	  SNMP ifindex: 1234, VRF: mgmt0
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 00:01:30
	  Description: 
	  MAC Address: 55:55:10:01:01:20
	  Speed: 1Gbps, Duplex: FULL
	  L2 MTU: 1514
	  IPv4 Address: 10.1.1.20/32
	  IPv6 Admin state: enabled
	  IPv6 local: fe80::6a05:caff:fe38:6f68/64, Status: Preferred
	  IPv6 Address: 2010::0001:0001:0001:0020/128, Status: Preferred
	  IPv4 DHCP: enabled, IPv6 DHCP: enabled
	  ARP Timeout: 3600 seconds
	  NDP Timeout: 3600 seconds 
	  Encapsulation: Ethernet
	  Access-list IPv4: In: N/A, Out: N/A
	  Access-list IPv6: In: N/A, Out: N/A
	

	dnRouter# show interfaces management mgmt-ncc-0
	
	Interface mgmt-ncc-0
	  SNMP ifindex: 1234
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 00:01:30
	  Description: internal mgmt.
	  MAC Address: 7c:fe:90:57:73:81 (HW: 7c:fe:90:57:73:81)
	  Speed: 1Gbps, Duplex: full
	  L2 MTU: 1514
	  IPv4 Address: 10.1.1.1/32 (DHCP)
	  IPv6 local: fe80::6a05:caff:fe38:6f68/64
	  IPv6 Address: 2010::0001:0001:0001:0020/128
	  IPv4 DHCP: enabled, IPv6 DHCP: enabled
	  ARP Timeout: 3600 seconds
	  NDP Timeout: 3600 seconds 
	  Encapsulation: Ethernet
	  Access-list IPv4: In: N/A
	  Access-list IPv6: In: N/A
	  Reason for last down state: link-down on mgmt-ncc-1/0
	  Members Information:
		| Interface    | Member State  |
		|--------------+---------------+
		| mgmt-ncc-0/0 | up            |
		| mgmt-ncc-0/1 | up            |

	
	dnRouter# show interfaces management mgmt-ncc-1/0

	Interface mgmt-ncc-1/0
	  SNMP ifindex: 1234, VRF: mgmt-ncc-1
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 00:01:30
	  Speed: 100Gbps, Duplex: FULL
	  Encapsulation: Ethernet
	

	dnRouter# show interfaces management console-ncc-0/0
	
	Interface console-ncc-0/0
	  SNMP ifindex: 1234,
	  Admin state: enabled 
	  Baud rate: 115200, Parity: None, Stop bits: 1, Data bits: 8, Flow control: None
	

	dnRouter# show interfaces management ipmi-ncc-0/0
	
	Interface ipmi-ncc-0/0
	  SNMP ifindex: 1234,
	  Admin state: enabled
	  MAC Address: 7c:fe:90:57:73:81
	  IPv4 Address: 10.1.1.1/32 (DHCP)
	   
	dnRouter# show interfaces management ipmi-ncc-0/0

	Interface ipmi-ncc-0/0
	  SNMP ifindex: 1234,
	  Admin state: enabled
	  MAC Address: 7c:fe:90:57:73:81
	  IPv4 Address: 10.1.1.1/32 (Static)
	  Default Gateway IP: 10.1.2.254

	dnRouter# show interfaces management ipmi-ncm-A0/0
	
	Interface ipmi-ncm-A0/0
	  SNMP ifindex: 1234,
	  Admin state: enabled
	  MAC Address: 7c:fe:90:57:73:81
	  IPv4 Address: 10.1.1.1/32 (DHCP)
	
	
.. **Help line:** Displays management interface information

**Command History**

+---------+---------------------------------------------------------------------------------------+
| Release | Modification                                                                          |
+=========+=======================================================================================+
| 11.0    | Command introduced                                                                    |
+---------+---------------------------------------------------------------------------------------+
| 16.2    | Moved all management interfaces to this command and exposed management bundle members |
+---------+---------------------------------------------------------------------------------------+

