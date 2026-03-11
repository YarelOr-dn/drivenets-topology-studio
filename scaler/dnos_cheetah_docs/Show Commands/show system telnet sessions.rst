show system telnet sessions
---------------------------

**Minimum user role:** viewer

To display the Telnet sessions that are currently active in the system:



**Command syntax: show system telnet sessions**

**Command mode:** operational



.. **Internal Note**

	- remote address is not supported for out-of-band Telnet sessions.

**Parameter table**

The following information is displayed on each Telnet session:

+----------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Field          | Description                                                                                                                    | Range                       |
+================+================================================================================================================================+=============================+
| Session ID     | The session's socket id                                                                                                        | 1..65535                    |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| User           | The telnet user name                                                                                                           | String                      |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Role           | The type of role of the user who initiated the telnet session                                                                  | Admin                       |
|                |                                                                                                                                | Operator                    |
|                |                                                                                                                                | Viewer                      |
|                |                                                                                                                                | Techsupport                 |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| VRF            | The Telnet session management type (in-band/out-of-band)                                                                       | default - in-band           |
|                |                                                                                                                                | mgmt0 - out-of-band         |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Remote Address | The IPv4/IPv6 address and TCP port number of the session initiator. The remote address is relevant to inband connections only. | X.X.X.X:Y                   |
|                | Remote address is not supported for out-of-band Telnet sessions                                                                | X.X.X.X - IPv4/IPv6 address |
|                |                                                                                                                                | Y - TCP port number         |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Session Uptime | The total amount of time that the session is up                                                                                | dd days, hh:mm:ss           |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Idle time      | The amount of time out of the session uptime that the telnet session has been idle                                             | hh:mm:ss                    |
+----------------+--------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show system telnet sessions

	Telnet Server Sessions:

	|   Session-ID | User   | Role      | VRF        | Remote Address   | Session Uptime   | Idle time  |
	|--------------+--------+-----------+------------+------------------+------------------+------------|
	|          714 | dnroot | Admin     | default    | 2.2.2.2:56356    | 1 day, 01:01:05  | 01:02:05   |
	|          748 | dnroot | Admin     | default    | 2.2.2.3:56364    | 2 days, 01:01:05 | 00:02:05   |
	|          777 | user1  | Operator  | mgmt0      | 5.5.2.3:54564    | 0 days, 05:21:20 | 00:00:10   |

	Telnet Client Sessions:

	|   Session-ID | VRF        | Remote Address   | Session Uptime   | Idle time  |
	|--------------+------------+------------------+------------------+------------|
	|          776 | default    | 1.1.1.1:23       | 1 day, 01:01:05  | 01:02:05   |
	|          806 | mgmt0      | 4.4.4.4:23       | 1 day, 01:01:05  | 00:02:05   |



.. **Help line:** show active telnet sessions in system.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
