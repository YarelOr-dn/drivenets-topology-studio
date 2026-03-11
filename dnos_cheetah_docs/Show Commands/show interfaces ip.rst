show interfaces ip
------------------

**Minimum user role:** viewer


The show interfaces ip command displays the IPv4 and IPv6 addresses of all interfaces. If you specify an interface name, the output result is filtered to show only the information for the requested interface.

**Command syntax: show interfaces ip** [interface-name]

**Command mode:** operational



**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle

	- Bundle vlan

	- Loopback

	- gre-tunnel

	- IRB

- Specify an interface to filter the displayed information to that interface.

.. - In the table IPv6 addresses will be marked as suspended (s) if they are in 'Tentative' or 'Duplicate' status (applicable to IPv6 addresses going through DAD procedure).


The following information is displayed per interface:

+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Field                      | Description                                                                                                                                                                                                      | Range        |
+============================+==================================================================================================================================================================================================================+==============+
| Interface                  | The name of the interface                                                                                                                                                                                        | String       |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Admin                      | The administrative status, indicates whether or not the interface is currently enabled.                                                                                                                          | Enabled      |
|                            | System-down means that the port was shut down by the system (and not by a user).                                                                                                                                 | Disabled     |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Operational                | The operational state of the interface, indicates whether the link is currently up or down. For physical interfaces, the operational state relates to the link-state (lasar state)                               | Up           |
|                            | Not-present: the port was pre-provisioned (the NCP is configured but not yet connected to the NCC), or the port was removed due to breakout.                                                                     | Down         |
|                            |                                                                                                                                                                                                                  | Not-present  |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| IPv4 Address               | The configured IPv4 address of the interface. Secondary IPv4 addresses are also listed.                                                                                                                          | A.B.C.D/x    |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| IPv6 Address               | The configured IPv6 address(es) of the interface. IPv6 addresses are marked as suspended (s) if they are have a 'Tentative' or 'Duplicate' status. (Applicable to IPv6 addresses going through a DAD procedure). | x:x::x:x/x   |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Reason for last down state | Displays the reason why the physical interface went down                                                                                                                                                         | string       |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+


**Example**
::

	dnRouter# show interfaces ip
	
	Legend: i - inner vlan, u - unnumbered interface, b - interface disabled due to breakout, L2 - l2 service interface, s - suspended IPv6 address, p - primary IP address (has secondaries), v - VLAN list or range (only lowest VID is displayed), d - obtained via DHCP

	| Interface       | Admin    | Operational | IPv4 Address    | IPv6 Address                   | Network-Service                                       |
	+-----------------+----------+-------------+-----------------+--------------------------------+-------------------------------------------------------+
	| bundle-3        | enabled  | up          | 30.1.1.1/30     | 2001:1234::1/122 (s)           | VRF (default)                                         |
	| bundle-3.200    | enabled  | up          | 30.4.4.1/30 (p) | 1006:abcd:12::2/128            | VPWS (cust1)                                          |
	| bundle-2        | enabled  | up          | 4.4.4.4/30      | 1004:abcd:12::2/128 (d)        | VRF (default)                                         |
	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30     | 1001:abcd:12::2/128            | VRF (default)                                         |
	| ge100-2/1/1.100 | enabled  | up          |                 |                                | BD (BD_1_3_INTERFACE_IRB_IPv4_default)                |
	| ge100-3/1/1     | enabled  | up          |                 |                                | VRF (MyVrf1)                                          |
	| lo1             | disabled | down        | 1.1.1.1/32      | 2001::0001:0001:0001:0001/128  | VRF (default)                                         |
	| irb1            | enabled  | up          | 60.60.0.6/29    |                                | VRF (default), BD (BD_1_3_INTERFACE_IRB_IPv4_default) |


	dnRouter# show interfaces ip ge100-2/1/1

	| Interface       | Admin    | Operational | IPv4 Address    | IPv6 Address                   | Network-Service                                       |
	+-----------------+----------+-------------+-----------------+--------------------------------+-------------------------------------------------------+
	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30     | 1001:abcd:12::2/128            | VRF (default)                                         |


.. **Help line:** Displays configured IPv4 or IPv6 addresses

**Command History**

+---------+-------------------------------------------------------------------------------+
| Release | Modification                                                                  |
+=========+===============================================================================+
| 5.1.0   | Command introduced                                                            |
+---------+-------------------------------------------------------------------------------+
| 6.0     | updated examples, removed eth0                                                |
+---------+-------------------------------------------------------------------------------+
| 10.0    | Updated examples, added mgmt0 and mgmt-ncc/0/0                                |
+---------+-------------------------------------------------------------------------------+
| 11.4    | Added support for GRE tunnels                                                 |
+---------+-------------------------------------------------------------------------------+
| 16.1    | Added support for VRF name in the output                                      |
+---------+-------------------------------------------------------------------------------+
| 16.2    | Moved management interfaces under the applicable command                      |
+---------+-------------------------------------------------------------------------------+
| 18.0    | Added support for IRB interfaces and network-service association information  |
+---------+-------------------------------------------------------------------------------+
| 19.1    | Added indication whether IP address was obtained via DHCP                     |
+---------+-------------------------------------------------------------------------------+