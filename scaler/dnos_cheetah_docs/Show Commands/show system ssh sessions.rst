show system ssh sessions 
-------------------------

**Minimum user role:** viewer

To display the SSH sessions that are currently active in the system:



**Command syntax: show system ssh sessions**

**Command mode:** operational



**Parameter table**

The following information is displayed on each SSH session:

+----------------+--------------------------------------------------------------------------------------------------------------------------------+
| Field          | Description                                                                                                                    |
+================+================================================================================================================================+
| Session ID     | The session's unique identifier                                                                                                |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+
| User           | The user who initiated the SSH session                                                                                         |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+
| VRF            | default          (in-band)                                                                                                     |
|                | non-default-vrf  (in-band)                                                                                                     |
|                | mgmt0        (out-of-band)                                                                                                     |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+
| Role           | The role of the user who initiated the SSH session                                                                             |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+
| Remote Address | The IPv4/IPv6 address and TCP port number of the session initiator. The remote address is relevant to inband connections only. |
|                | Remote address is not supported for out-of-band SSH sessions                                                                   |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+
| Session Uptime | The total amount of time that the session is up (dd days, hh:mm:ss)                                                            |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+
| Idle time      | The amount of time out of the session uptime that the SSH session has been idle (hh:mm:ss)                                     |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system ssh sessions

	SSH Server Sessions:

	|   Session-ID | User   | Role      | VRF        | Remote Address   | Session Uptime   | Idle time  |
	|--------------+--------+-----------+------------+------------------+------------------+------------|
	|          714 | dnroot | Admin     | default    | 2.2.2.2:56356    | 1 day, 01:01:05  | 01:02:05   |
	|          748 | dnroot | Admin     | default    | 2.2.2.3:56364    | 2 days, 01:01:05 | 00:02:05   |
	|          777 | user1  | Operator  | mgmt0      | 3.4.2.3:43564    | 0 days, 05:21:20 | 00:00:10   |
	|          797 | user1  | Operator  | my_vrf     | 3.3.3.3:43574    | 0 days, 05:21:20 | 00:00:10   |
	
	SSH Client Sessions:
	
	|   Session-ID | User   | Role      | VRF        | Remote Address   | Session Uptime   | Idle time  |
	|--------------+--------+-----------+------------+------------------+------------------+------------|
	|          776 | test   |           | default    | 1.1.1.1:22       | 1 day, 01:01:05  | 01:02:05   |
	|          806 | test2  |           | mgmt0      | 5.2.3.3:22       | 1 day, 01:01:05  | 00:02:05   |
    |          771 | user   |           | my-vrf     | 1.1.1.1:22       | 0 days, 05:21:20 | 00:00:10   |
	
	

.. **Help line:** show active ssh sessions in system.

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 5.1.0   | Command introduced                               |
+---------+--------------------------------------------------+
| 6.0     | Updated to include strict-user and role          |
+---------+--------------------------------------------------+
| 10.0    | Removed strict-user                              |
+---------+--------------------------------------------------+
| 11.0    | Added session uptime and idle time to the output |
+---------+--------------------------------------------------+
| 13.1    | Updated VRF domain per session                   |
+---------+--------------------------------------------------+
| 19.1    | Add support in NDVRF                             |
+---------+--------------------------------------------------+

