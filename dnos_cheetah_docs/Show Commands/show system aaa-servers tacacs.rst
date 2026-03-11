show system aaa-servers tacacs
-------------------------------

**Minimum user role:** viewer

Use the following show commands to verify that the TACACS+ servers are properly configured:



**Command syntax: show system aaa-servers tacacs** [ip-address]

**Command mode:** operational



..
	**Internal Note**

	- If ip-address parameter is not specified, information for all AAA servers is presented

	- For not available AAA servers, remaining retry-time is presented till next availability check

	- If all AAA servers are not available, a remaining hold-down timer is presented till the next AAA attempt

	- If AAA server was never accessed by DNOS, its operational state appears as empty, since its state is unknown. The same correct for AAA server with exceeded retry timer that wasn't conntaced yet

	- vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

**Parameter table**

+------------+---------------------------------------------------------------------------------+----------+
| Parameter  | Description                                                                     | Range    |
+============+=================================================================================+==========+
| ip-address | Filters the display by the IPv4 or IPv6 address of the specific TACACS+ server. | A.B.C.D  |
|            |                                                                                 | x:x::x:x |
+------------+---------------------------------------------------------------------------------+----------+

For every server, the following information is displayed:

+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Field                | Description                                                                                                                                                                                                  | Range                                                             |
+======================+==============================================================================================================================================================================================================+===================================================================+
| AAA Function         | The functions on the supporting server                                                                                                                                                                       | Comma separated list of authentication, authorization, accounting |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| TACACS Admin State   | The administrative state of the AAA option. If it is disabled, then local users are used.                                                                                                                    | Enabled                                                           |
|                      |                                                                                                                                                                                                              | Disabled                                                          |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Priority             | The configured priority of the TACACS+ server (see system aaa-server tacacs server). When multiple servers are configured, the server with the higher priority (lower configured number) is attempted first. | 1..255                                                            |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Server               | The type of server used for the AAA.                                                                                                                                                                         | TACACS                                                            |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| IP Address           | The IPv4 or IPv6 address of the AAA server. See system aaa-server tacacs server.                                                                                                                             | A.B.C.D                                                           |
|                      |                                                                                                                                                                                                              | x:x::x:x                                                          |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| VRF                  | The TACACS server management type                                                                                                                                                                            | default         - in-band                                         |
|                      |                                                                                                                                                                                                              | non-default-vrf - out-of-band                                     |
|                      |                                                                                                                                                                                                              | mgmt0           - out-of-band                                     |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Operational          | The operational state of the AAA server. If AAA server was never accessed by DNOS or if the server is not connected beyond the retry-time, its operational state appears as empty (its state is unknown).    | Active                                                            |
|                      |                                                                                                                                                                                                              | Not available                                                     |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Port                 | The TCP port number used when making connections to the AAA server. See system aaa-server tacacs server port.                                                                                                | 0..65535                                                          |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Timeout              | The amount of time (in seconds) the device waits to receive a response from the AAA server before it assumes that the server is unavailable. See system aaa-server tacacs server timeout.                    | 1..1000                                                           |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Retry-time           | The configured retry-time (see system aaa-server tacacs timers)                                                                                                                                              | 0..3600                                                           |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Remaining Retry-Time | When the AAA server is unavailable, this timer displays the amount of time remaining (in seconds) till the next availability check                                                                           | 0..3600                                                           |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Hold-down            | The configured hold-down (see system aaa-server tacacs timers)                                                                                                                                               | 0..1200                                                           |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Remaining hold-down  | When all AAA servers are unavailable, this timer displays the amount of time remaining (in seconds) for the NCR to suppress any TACACS+ requests. This timer is displayed until the next AAA attempt.        | 0..1200                                                           |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Authorization Type   | The TACACS authorization type if the authorization type is 'session', means will be done according to the authorization as was received from the server.                                                     | session                                                           |
|                      | If 'session' type is used, authorization requests will be done according to the authorization as was received from the server.                                                                               | command                                                           |
|                      | If 'session-and-command' type is used, session authorization will be applied first, than command authorization will be performed for every cli command executed by the user.                                 | session-and-command                                               |
+----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+

**Example**
::

	dnRouter# show system aaa-servers tacacs

	TACACS admin state: enable
	Timers: retry-time: 1200 seconds, hold-down: 600 seconds
	Autherization Type: session

	| Priority | AAA Function   | Server | IP Address  | Vrf         | Operational   | Port | Timeout | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+---------+----------------------|
	| 1        | authorization  | tacacs | 1.1.1.1     | default     | not available | 49   | 5       | 54 seconds           |
	| 2        | authorization, | tacacs | 5.5.5.5     | default     | active        | 50   | 5       |                      |
	|          | accounting     | tacacs | 5.5.5.5     | default     | active        | 50   | 5       |                      |
	| 3        | accounting     | tacacs | 192.168.1.2 | mgmt0       |               | 100  | 5       |                      |
	| 4        | authorization, | tacacs | 192.168.1.3 | my_vrf      |               | 17   | 5       |                      |
	|          | accounting     | tacacs | 192.168.1.3 | my_vrf      |               | 17   | 5       |                      |
	| 5        | authorization  | tacacs | 1134:1134::1| mgmt0       |               | 33   | 5       |                      |


	dnRouter# show system aaa-servers tacacs

	TACACS admin state: enable
	Timers: retry-time: 1200 seconds, hold-down: 600 seconds (124 seconds remaining)
	Autherization Type: session

	| Priority | AAA Function   | Server | IP Address  | Vrf         | Operational   | Port | Timeout | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+---------+----------------------|
	| 1        | authorization  | tacacs | 1.1.1.1     | default     |               | 49   | 5       |                      |
	| 2        | authorization, | tacacs | 5.5.5.5     | default     | not available | 50   | 5       | 120 seconds          |
	|          | accounting     | tacacs | 5.5.5.5     | default     | not available | 50   | 5       | 130 seconds          |
	| 3        | accounting     | tacacs | 192.168.1.2 | mgmt0       | not available | 100  | 5       | 150 seconds          |
	| 4        | authorization, | tacacs | 192.168.1.3 | my_vrf      | not available | 17   | 5       | 600 seconds          |
	|          | accounting     | tacacs | 192.168.1.3 | my_vrf      | active        | 17   | 5       |                      |
	| 5        | authorization  | tacacs | 1134:1134::1| mgmt0       | not available | 33   | 5       | 600 seconds          |


	dnRouter# show system aaa-servers tacacs 1.1.1.1

	TACACS admin state: enable

	| Priority | AAA Function   | Server | IP Address  | Vrf         | Operational   | Port | Timeout | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+---------+----------------------|
	| 1        | authorization  | tacacs | 1.1.1.1     | default     | active        | 49   | 5       |                      |

	dnRouter# show system aaa-servers tacacs 1134:1134::1

	TACACS admin state: enable

	| Priority | AAA Function   | Server | IP Address  | Vrf         | Operational   | Port | Timeout | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+---------+----------------------|
	| 1        | authorization  | tacacs | 1134:1134::1| mgmt0       | not available | 49   | 5       | 600 seconds          |




.. **Help line:** show system aaa-servers tacacs

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 5.1.0   | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+
| 6.0     | Updated the command and examples                                                  |
+---------+-----------------------------------------------------------------------------------+
| 11.0    | Added timers display (retry-time and hold-down)                                   |
+---------+-----------------------------------------------------------------------------------+
| 13.1    | Renamed management Type in-band as default VRF, and Type out-of-band as mgmt0 VRF |
+---------+-----------------------------------------------------------------------------------+
| 15.1    | Added support for IPv6 address format and added new AAA Function column           |
+---------+-----------------------------------------------------------------------------------+
| 18.0.2  | Added support for TACACS command authorization                                    |
+---------+-----------------------------------------------------------------------------------+
| 19.1    | Added non default VRF support                                                     |
+---------+-----------------------------------------------------------------------------------+
