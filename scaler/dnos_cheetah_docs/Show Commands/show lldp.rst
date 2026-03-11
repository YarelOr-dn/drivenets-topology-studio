show lldp
---------

**Minimum user role:** viewer

To the LLDP local system information:



**Command syntax: show lldp**

**Command mode:** operational



.. **Note**

	- The supported TLV and System capabilities values are fixed.

**Parameter table**

The following information is displayed for the system:

+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Parameter           | Description                                                                                                     | Range               | Default     |
+=====================+=================================================================================================================+=====================+=============+
| System Name         | The configured name of the system. See system name.                                                             | 1..255 characters   | \-          |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Chassis ID          | The unique identifier of the chassis.                                                                           | 1..255 characters   | \-          |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Chassis ID Type     | The type of ID used for the chassis.                                                                            | MAC Address         | MAC Address |
|                     |                                                                                                                 | IfAlias             |             |
|                     |                                                                                                                 | entPhysicalAlias    |             |
|                     |                                                                                                                 | Mgmt Address        |             |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| System Description  | The description configured for the system. See system info description                                          | 1..255 characters   | \-          |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| System Capabilities | The information regarding the system's capabilities                                                             | Bridge              | \-          |
|                     |                                                                                                                 | Router              |             |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Keep-alive          | The configured keep-alive timer (in seconds). See lldp timers.                                                  | 30..65535           | 30          |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Hold-time           | The configured hold-time timer (in seconds). See lldp timers.                                                   | 30..65535           | 120         |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| TLV                 | The supported optional TLVs.                                                                                    | Port Description    | \-          |
|                     |                                                                                                                 | System Name         |             |
|                     |                                                                                                                 | System Description  |             |
|                     |                                                                                                                 | System Capabilities |             |
|                     |                                                                                                                 | Management Address  |             |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Status              | Displays the configured admin-state of the LLDP TLV transmission on the system per each optional TLV.           | Enabled             | Enabled     |
|                     |                                                                                                                 | Disabled            |             |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Interface           | The name of the LLDP enabled physical interface                                                                 | Physical interface  | \-          |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Transmit            | Displays the configured admin-state of the LLDP message transmission capability of the LLDP enabled interfaces. | Enabled             | Enabled     |
|                     |                                                                                                                 | Disabled            |             |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Receive             | Displays the configured admin-state of the LLDP message receipt capability of the LLDP enabled interfaces.      | Enabled             | Enabled     |
|                     |                                                                                                                 | Disabled            |             |
+---------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+

**Example**
::

	dnRouter# show lldp

	System Name: dn1-Local-Router
	Chassis ID: aa:bb:cc:dd:ee:01 (Type: MAC Address)
	System Description: DRIVENETS LTD. Virtual Router, DNOS [10.0.0.1]
	System Capabilities: Bridge, Router

	Timers
	  Keep-alive: 30 (seconds)
	  Hold-time: 120 (seconds)

	Supported TX for optional TLVs:
	| TLV                 | Status   |
	|---------------------+----------|
	| Port Description    | enabled  |
	| System Name         | enabled  |
	| System Description  | enabled  |
	| System Capabilities | disabled |
	| Management Address  | disabled |

	Interfaces:
	| Interface   | Transmit | Receive  |
	|-------------+----------|----------|
	| ge100-1/2/3 | enabled  | enabled  |
	| ge100-4/2/1 | enabled  | disabled |



.. **Help line:** show lldp

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 7.0     | Command introduced            |
+---------+-------------------------------+
| 9.0     | Not supported in this version |
+---------+-------------------------------+
| 10.0    | Supported.                    |
+---------+-------------------------------+
| 16.1    | Added TLV-filter status       |
+---------+-------------------------------+
