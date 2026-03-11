show system aaa-servers radius 
-------------------------------

**Minimum user role:** viewer

Use the following show commands to verify that the RADIUS servers are properly configured:



**Command syntax: show system aaa-servers radius** [ip-address]

**Command mode:** operational



.. 
	**Internal Note**

	- If ip-address parameter is not specified, information for all RADIUS servers is presented

	- For not available servers, the remaining retry-time till the server may be tried again on future logins is presented

	- If all AAA servers are not available, the remaining hold-down time till any of the servers may be tried again on future logins is presented 

	- If AAA server was never accessed by DNOS, its operational state appears as empty, since its state is unknown. The same correct for AAA server with exceeded retry timer that wasn't contacted yet

	- vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

**Parameter table**

+------------+------------------------------------------------------------------------+---------+
| Parameter  | Description                                                            | Range   |
+============+========================================================================+=========+
| ip-address | Filters the display by the IPv4 address of the specific RADIUS server. | A.B.C.D |
+------------+------------------------------------------------------------------------+---------+

For every server, the following information is displayed:

+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Field                | Description                                                                                                                                                                                                | Range                                                             |
+======================+============================================================================================================================================================================================================+===================================================================+
| AAA Function         | The functions on the supporting server                                                                                                                                                                     | Comma separated list of authentication, authorization, accounting |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Server               | The type of server used for the AAA (Authentication only)                                                                                                                                                  | RADIUS                                                            |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| IP Address           | The IPv4/IPv6 address of the AAA server.                                                                                                                                                                   | A.B.C.D                                                           |
|                      |                                                                                                                                                                                                            | x:x::x:x                                                          |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| VRF                  | Defines whether the server is in-band or out-of-band                                                                                                                                                       | default - in-band                                                 |
|                      |                                                                                                                                                                                                            | mgmt0 - out-of-band                                               |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Operational          | The operational state of the AAA server. If AAA server was never accessed by DNOS or if the server was not contacted beyond the retry-time, its operational state appears as empty (its state is unknown). | Active                                                            |
|                      |                                                                                                                                                                                                            | Not available                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Port                 | The TCP port number used when making connections to the AAA server.                                                                                                                                        | 0..65535                                                          |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Retry-interval       | The configured time between retries.                                                                                                                                                                       | 1..1000 (seconds)                                                 |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Remaining Retry-Time | When the AAA server is unavailable, this timer displays the amount of time remaining (in seconds) till the server may be tried again on future logins                                                      | 0..3600                                                           |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+
| Retries              | The number of times to retry connection to the server                                                                                                                                                      | 1..50                                                             |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+

**Example**
::

	dnRouter# show system aaa-servers radius 
	
	Timers: retry-time: 1200 seconds, hold-down: 600 seconds
	
	| Priority | AAA Function   | Server | IP Address  | Vrf         | Operational   | Port | Retry Interval | Retries | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+----------------+---------+----------------------|
	| 1        | authentication | radius | 1.1.1.1     | default     | not available | 49   | 5 seconds      | 3       | 54 seconds           |
	| 2        | authentication | radius | 5.5.5.5     | default     | active        | 50   | 5 seconds      | 3       |                      |
	| 3        | authentication | radius | 192.168.1.2 | mgmt0       | active        | 100  | 5 seconds      | 3       |                      |
	| 4        | authentication | radius | 192.168.1.3 | mgmt0       |               | 17   | 5 seconds      | 3       |                      |
	|          | authorization  |        |             |             |               |      |                |         |                      |
	| 5        | authentication | radius | 1134:1134::1| mgmt0       |               | 33   | 5 seconds      | 3       |                      |

	
	dnRouter# show system aaa-servers radius 
	
	Timers: retry-time: 1200 seconds, hold-down: 600 seconds (124 seconds remaining)
	
	| Priority | AAA Function   | Server | IP Address  | Vrf         | Operational   | Port | Retry Interval | Retries | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+----------------+---------+----------------------|
	| 1        | authentication | radius | 1.1.1.1     | default     | not available | 49   | 5 seconds      | 3       |                      |
	| 2        | authentication | radius | 5.5.5.5     | default     | not available | 50   | 5 seconds      | 3       |                      |
	| 3        | authentication | radius | 192.168.1.2 | mgmt0       | not available | 100  | 5 seconds      | 3       |                      |
	| 4        | authentication,| radius | 192.168.1.3 | mgmt0       | not available | 17   | 5 seconds      | 3       |                      |
	|          | authorization  |        |             |             |               |      |                |         |                      |
	| 5        | authentication | radius | 1134:1134::1| mgmt0       | not available | 33   | 5 seconds      | 3       |                      |
	
	dnRouter# show system aaa-servers radius 1.1.1.1
	
	| Priority | AAA Function   | Server | IP Address  | Vrf         | Operational   | Port | Retry Interval | Retries | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+----------------+---------+----------------------|
	| 1        | authentication | radius | 1.1.1.1     | default     | not available | 49   | 5 seconds      | 3       | 700 seconds          |

	dnRouter# show system aaa-servers radius 1134:1134::1

	| Priority | AAA Function   | Server | IP Address  | Vrf         | Operational   | Port | Retry Interval | Retries | Remaining Retry-Time |
	|----------+----------------+--------+-------------+-------------+---------------+------+----------------+---------+----------------------|
	| 5        | authentication | radius | 1134:1134::1| mgmt0       | not available | 33   | 5 seconds      | 3       |                      |

	
	

.. **Help line:** show system aaa-servers radius

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 13.0    | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+
| 13.1    | Renamed management Type in-band as default VRF, and Type out-of-band as mgmt0 VRF |
+---------+-----------------------------------------------------------------------------------+
| 15.1    | Added support for IPv6 address format                                             |
+---------+-----------------------------------------------------------------------------------+

