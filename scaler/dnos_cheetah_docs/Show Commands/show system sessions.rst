show system sessions
-------------------------

**Minimum user role:** viewer

Displays the system's TCP and UDP sessions (for in-band and out-of-band management networks):



**Command syntax: show system sessions** [tcp \| udp]

**Command mode:** operational



**Note**

- Use the tcp or udp options to display only TCP or UDP sessions (respectively). If no protocol is specified, sessions for both UDP and TCP are presented (for IPv4 and IPv6 addresses).

.. - command presents control and management TCP/UDP sessions for in-band management network only.

	- if no specific protocol is specified, sessions for both UDP and TCP are presented

	- Sessions shown for ipv4 and ipv6 addresses

	- Output shown without DNS resolution (i.e using netstat -p tcp -ant flag)

	- If protocol is UDP, no state will appear

	- If remote address unknown/UDP,  *.* will appear

**Parameter table**

For each session, the following information is displayed:

+-----------------+---------------------------------------------------+-------------------+
| Parameter       | Description                                       | Range             |
+=================+===================================================+===================+
| VRF             | The session management domain                     | default           |
|                 |                                                   | mgmt0             |
|                 |                                                   | mgmt-ncc-1        |
|                 |                                                   | mgmt-ncc-0        |
+-----------------+---------------------------------------------------+-------------------+
| Protocol        | The protocol of the session                       | TCP               |
|                 |                                                   | UDP               |
+-----------------+---------------------------------------------------+-------------------+
| Local address   | The local address of the session                  | IPv4-address:Port |
|                 |                                                   | IPv6-address:Port |
+-----------------+---------------------------------------------------+-------------------+
| Remote address  | The remote address of the session                 | IPv4-address:Port |
|                 |                                                   | IPv6-address:Port |
+-----------------+---------------------------------------------------+-------------------+
| State           | The state of the session                          | ESTABLISHED       |
|                 |                                                   | SYN_SENT          |
|                 |                                                   | SYN_RECV          |
|                 |                                                   | FIN_WAIT1         |
|                 |                                                   | FIN_WAIT2         |
|                 |                                                   | TIME_WAIT         |
|                 |                                                   | CLOSE             |
|                 |                                                   | CLOSE_WAIT        |
|                 |                                                   | LAST_ACK          |
|                 |                                                   | LISTEN            |
|                 |                                                   | CLOSING           |
|                 |                                                   | UNKNOWN           |
+-----------------+---------------------------------------------------+-------------------+
| Uptime          | The amount of time that the session has been up   | DD days, HH:MM:SS |
+-----------------+---------------------------------------------------+-------------------+
| Local MSS       | The MSS of the local TCP session (in bytes)       | 0..9000           |
+-----------------+---------------------------------------------------+-------------------+
| Established MSS | The MSS of the established TCP session (in bytes) | 0..9000           |
+-----------------+---------------------------------------------------+-------------------+

**Example**
::

	dnRouter# show system sessions

	| Vrf          | Protocol   | Local Address           | Remote Address          | State       | Uptime           | Local MSS   | Established MSS   |
	|--------------+------------+-------------------------+-------------------------+-------------+------------------+-------------+-------------------|
	| mgmt0        | TCP        | :::50051                | :::*                    | LISTEN      |                  |             |                   |
	| mgmt0        | TCP        | :::830                  | :::*                    | LISTEN      |                  |             |                   |
	| mgmt0        | TCP        | :::22                   | :::*                    | LISTEN      |                  |             |                   |
	| mgmt0        | TCP        | :::21                   | :::*                    | LISTEN      |                  |             |                   |
	| mgmt0        | TCP        | 0.0.0.0:830             | 0.0.0.0:*               | LISTEN      |                  |             |                   |
	| mgmt0        | TCP        | 0.0.0.0:22              | 0.0.0.0:*               | LISTEN      |                  |             |                   |
	| mgmt-ncc-0   | TCP        | :::2222                 | :::*                    | LISTEN      |                  |             |                   |
	| mgmt-ncc-0   | TCP        | :::22                   | :::*                    | LISTEN      |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:59220       | 100.64.9.199:4505       | ESTABLISHED | 3 days, 22:17:57 | 1462        | 1448              |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:40506       | 100.64.1.169:4505       | ESTABLISHED | 3 days, 22:17:57 | 1462        | 1448              |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:40354       | 100.64.9.199:5000       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:38950       | 100.64.1.169:4506       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:38932       | 100.64.1.169:4506       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:38900       | 100.64.1.169:4506       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:38898       | 100.64.1.169:4506       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:38896       | 100.64.1.169:4506       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:36838       | 100.64.9.199:4506       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:36836       | 100.64.9.199:4506       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:36822       | 100.64.9.199:4506       | TIME_WAIT   |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 100.64.6.98:22          | 100.64.8.98:51017       | ESTABLISHED | 0 days, 17:58:17 | 1474        | 1460              |
	| mgmt-ncc-0   | TCP        | 0.0.0.0:2222            | 0.0.0.0:*               | LISTEN      |                  |             |                   |
	| mgmt-ncc-0   | TCP        | 0.0.0.0:22              | 0.0.0.0:*               | LISTEN      |                  |             |                   |
	| default      | TCP        | :::50051                | :::*                    | LISTEN      |                  |             |                   |
	| default      | TCP        | :::2606                 | :::*                    | LISTEN      |                  |             |                   |
	| default      | TCP        | :::830                  | :::*                    | LISTEN      |                  |             |                   |
	| non-default1 | TCP        | :::830                  | :::*                    | LISTEN      |                  |             |                   |
	| default      | TCP        | :::179                  | :::*                    | LISTEN      |                  |             |                   |
	| non-default1 | TCP        | :::179                  | :::*                    | LISTEN      |                  |             |                   |
	| non-default2 | TCP        | :::179                  | :::*                    | LISTEN      |                  |             |                   |




	dnRouter# show system sessions tcp

	| VRF            | Protocol | Local address  | Remote Address | State        | Uptime            | Local MSS | Established MSS |
	|----------------+----------+----------------+----------------+--------------+-------------------+-----------+-----------------|
	| default        | TCP      | 10.1.1.1:179   | 1.1.1.1:22214  | ESTABLISHED  | 10 Days, 00:01:30 | 1500      | 1500            |
	| mgmt0          | TCP      | 10.1.1.1:21231 | 1.1.1.1:179    | ESTABLISHED  | 10 Days, 00:01:30 | 1500      | 1500            |


.. **Help line:** displays TCP and UDP sessions per system.

**Command History**

+---------+-----------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                    |
+=========+=================================================================================================================+
| 13.0    | Command introduced                                                                                              |
+---------+-----------------------------------------------------------------------------------------------------------------+
| 13.1    | Added OOB support: VRF type (in-band/out-of-band) per session and removed the Remote MSS column from the output |
+---------+-----------------------------------------------------------------------------------------------------------------+
| 16.1    | Added support for the display of non-default VRF sessions in the output of the command                          |
+---------+-----------------------------------------------------------------------------------------------------------------+
