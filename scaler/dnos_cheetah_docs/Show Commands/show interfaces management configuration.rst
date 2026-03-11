show interfaces management configuration
----------------------------------------

**Minimum user role:** viewer

To display the configuration of the physical management interfaces:

**Command syntax: show interfaces management configuration**

**Command mode:** operational

**Parameter table**

The following information is displayed for each interface:

+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
|                      |                                                                                                                                              |
| Parameter            | Description                                                                                                                                  |
+======================+==============================================================================================================================================+
|                      |                                                                                                                                              |
| Admin-state          | Displays whether the interface/port is enabled or disabled.                                                                                  |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
|                      |                                                                                                                                              |
| Description          | The configured description for the interface/port                                                                                            |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
|                      |                                                                                                                                              |
| MAC Address          | The interface’s MAC address                                                                                                                  |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
|                      |                                                                                                                                              |
| MTU                  | The configured MTU for the interface                                                                                                         |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
|                      |                                                                                                                                              |
| IPv4/IPv6 Address    | The static IPv4 or IPv6 address configured for the interface. DHCP indicates that the IP address is obtained dynamically through DHCP        |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
|                      |                                                                                                                                              |
| IPv4 routes          | The installed routes for packet forwarding                                                                                                   |
+----------------------+----------------------------------------------------------------------------------------------------------------------------------------------+

**Note**

- This command is applicable to the mgmt-ncc interfaces.

**Example**
::

	dnRouter# show interfaces management configuration
	Interface mgmt-ncc-0
	Admin state: enabled
	Description:
	MAC Address: 06:6f:87:c9:67:2f
	MTU: 1500
	IPv4 Address: 100.64.6.37/20
	IPv6 Address: DHCP
	IPv4 routes:
		1.2.3.4/32 next-hop 4.2.3.1
		6.6.6.6/32 next-hop 4.2.3.1
	IPv6 routes:
		N/A
		
	Interface mgmt-ncc-0/0
		Admin state: enabled
		Description:
	
	Interface mgmt-ncc-0/1
		Admin state: enabled
		Description:

	Interface mgmt-ncc-1
	Admin state: enabled
	Description:
	MAC Address: 06:6f:87:c9:67:2f
	MTU: 1500
	IPv4 Address: DHCP
	IPv6 Address: DHCP
	IPv4 routes:
		N/A
	IPv6 routes:
		N/A
		
	Interface mgmt-ncc-1/0
		Admin state: enabled
		Description:
	
	Interface mgmt-ncc-1/1
		Admin state: enabled
		Description:


.. **Help line: show interfaces management configuration**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
