show system aaa-servers
-----------------------

**Minimum user role:** viewer

Use the following show commands to verify that the TACACS+ or RADIUS servers are properly configured:



**Command syntax: show system aaa-servers**

**Command mode:** operational



..
	**Internal Note**

	- If ip-address parameter is not specified, information for all TACACS servers is presented

	- For not available servers, the remaining retry-time till the server may be tried again on future logins is presented

	- If all the servers supporting certain AAA function are not available, the remaining hold-down time till any of the servers may be tried again on future logins is presented

	- If AAA server was never accessed by DNOS, its operational state appears as empty, since its state is unknown. The same correct for AAA server with exceeded retry timer that wasn't contacted yet

	- vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management, "my_vrf represents the non-default in-band management vrf.

**Parameter table**

For every server, the following information is displayed:

+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Field                                      | Description                                                                                                                                                                                                | Range                                                             |
+============================================+============================================================================================================================================================================================================+===================================================================+
| AAA Function                               | The functions on the supporting server                                                                                                                                                                     | Comma separated list of authentication, authorization, accounting |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Server                                     | The type of server used for the AAA.                                                                                                                                                                       | TACACS                                                            |
|                                            |                                                                                                                                                                                                            | RADIUS (Authentication only)                                      |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| IP Address                                 | The IPv4/IPv6 address of the AAA server.                                                                                                                                                                   | A.B.C.D                                                           |
|                                            |                                                                                                                                                                                                            | x:x::x:x                                                          |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Operational                                | The operational state of the AAA server. If AAA server was never accessed by DNOS or if the server was not contacted beyond the retry-time, its operational state appears as empty (its state is unknown). | Active                                                            |
|                                            |                                                                                                                                                                                                            | Not available                                                     |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Type                                       | Defines whether the server is in-band or out-of-band                                                                                                                                                       | in-band/out-of-band                                               |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Port                                       | The TCP/UDP destination port number used when making connections to the AAA server.                                                                                                                        | 0..65535                                                          |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Timeout (only for TACACS server)           | The amount of time (in seconds) the device waits to receive a response from the AAA server before it assumes that the server is unavailable.                                                               | 1..1000 (seconds)                                                 |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Retry-interval (only for RADIUS server)    | The configured time between retries.                                                                                                                                                                       | 1..1000 (seconds)                                                 |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Remaining Retry-Time                       | When the AAA server is unavailable, this timer displays the amount of time remaining (in seconds) till the server may be tried again on future logins                                                      | 0..3600                                                           |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Retries (only for RADIUS server)           | The number of times to retry connection to the server                                                                                                                                                      | 1..50                                                             |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Authorization Type (only for TACACS server)| The TACACS authorization type if the authorization type is 'session', means will be done according to the authorization as was received from the server.                                                   | session                                                           |
|                                            | If 'session' type is used, authorization requests will be done according to the authorization as was received from the server.                                                                             | command                                                           |
|                                            | If 'sessions-and-command' type is used, session authorization will be applied first, than command authorization will be performed for every cli command executed by the user.                              | session-and-command                                               |
+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+

sessions-and-command
**Example**
::

	dnRouter# show system aaa-servers

	Remote AAA admin state:     enabled
	Remaining hold-down time:   124 seconds

	RADIUS servers

	Timers: retry-time: 1200 seconds, hold-down: 600 seconds

	| Priority | AAA Function   | Server | IP Address  | VRF         | Operational   | Port | Retry Interval | Retries | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+----------------+---------+----------------------|
	| 1        | authentication | radius | 1.1.1.1     | default     | not available | 49   | 5 seconds      | 3       | 54 seconds           |
	| 2        | authentication | radius | 5.5.5.5     | default     | active        | 50   | 5 seconds      | 3       |                      |
	| 3        | authentication | radius | 192.168.1.2 | mgmt0       |               | 100  | 5 seconds      | 3       |                      |
	| 4        | authentication | radius | 192.168.1.3 | my_vrf      |               | 17   | 5 seconds      | 3       |                      |
	| 5        | authentication | radius | 1134:1134::1| mgmt0       |               | 33   | 5 seconds      | 3       |                      |

	TACACS servers

	Timers: retry-time: 1200 seconds, hold-down: 600 seconds (124 seconds remaining)
	Autherization Type: session

	| Priority | AAA Function   | Server | IP Address  | VRF         | Operational   | Port | Timeout | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+---------+----------------------|
	| 1        | authorization  | tacacs | 1.1.1.1     | default     | active        | 49   | 5       |                      |
	| 2        | authorization, | tacacs | 5.5.5.5     | default     | not available | 50   | 5       |                      |
	|          | accounting     | tacacs | 5.5.5.5     | default     | not available | 50   | 5       |                      |
	| 3        | accounting     | tacacs | 4.4.4.4     | mgmt0       | not available | 100  | 5       |                      |
	| 4        | authorization, | tacacs | 192.168.1.3 | my_vrf      | not available | 17   | 5       |                      |
	|          | accounting     | tacacs | 192.168.1.3 | my_vrf      | active        | 17   | 5       |                      |
	| 5        | authorization  | tacacs | 1134:1134::1| default     | not available | 66   | 5       |                      |


	dnRouter# show system aaa-servers

	Remote AAA admin state:     enabled
	Remaining hold-down time:   124 seconds

	RADIUS servers

	Timers: retry-time: 1200 seconds, hold-down: 600 seconds

	| Priority | AAA Function   | Server | IP Address  | VRF         | Operational   | Port | Retry Interval | Retries | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+----------------+---------+----------------------|
	| 1        | authentication,| radius | 1.1.1.1     | default     | not available | 49   | 5 seconds      | 3       | 54 seconds           |
	|          | authorization  |        |             |             |               |      |                |         |                      |
	| 2        | authentication,| radius | 5.5.5.5     | default     | active        | 50   | 5 seconds      | 3       |                      |
	|          | authorization  |        |             |             |               |      |                |         |                      |
	| 3        | authentication,| radius | 192.168.1.2 | mgmt0       |               | 100  | 5 seconds      | 3       |                      |
	|          | authorization  |        |             |             |               |      |                |         |                      |
	| 4        | authentication,| radius | 192.168.1.3 | my_vrf      |               | 17   | 5 seconds      | 3       |                      |
	|          | authorization  |        |             |             |               |      |                |         |                      |
	| 5        | authentication,| radius | 1134:1134::1| mgmt0       |               | 33   | 5 seconds      | 3       |                      |
	|          | authorization  |        |             |             |               |      |                |         |                      |

	TACACS servers

	Timers: retry-time: 1200 seconds, hold-down: 600 seconds (124 seconds remaining)
	Autherization Type: session

	| Priority | AAA Function   | Server | IP Address  | VRF         | Operational   | Port | Timeout | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+---------+----------------------|
	| 1        | accounting     | tacacs | 5.5.5.5     | default     | not available | 50   | 5       |                      |
	| 2        | accounting     | tacacs | 4.4.4.4     | mgmt0       | not available | 100  | 5       |                      |
	| 3        | accounting     | tacacs | 192.168.1.3 | my_vrf      | active        | 17   | 5       |                      |


.. **Help line:** show system aaa-servers

**Command History**

+---------+------------------------------------------------+
| Release | Modification                                   |
+=========+================================================+
| 13.0    | Command introduced                             |
+---------+------------------------------------------------+
| 15.1    | Added support for IPv6 address format          |
+---------+------------------------------------------------+
| 18.0.2  | Added support for TACACS command authorization |
+---------+------------------------------------------------+
| 19.1    | Added non default VRF support                  |
+---------+------------------------------------------------+
