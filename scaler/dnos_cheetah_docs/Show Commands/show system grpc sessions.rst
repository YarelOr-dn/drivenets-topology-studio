show system grpc sessions
-------------------------

**Minimum user role:** viewer

To display the active gRPC sessions in the system:

**Command syntax: show system grpc sessions** [session-id]

**Command mode:** operational



**Note**

- Rate is not presented for GET sessions.

.. - command without specified session-id will output all active gRPC sessions

	- Presented GET sessions are requests that were not yet fully replied by DNOS gNMI server

	- Rate is not presented for GET sessions

**Parameter table**

+------------+----------------------------------------------------------------------------------+----------+
| Parameter  | Description                                                                      | Range    |
+============+==================================================================================+==========+
| session-id | Optionally filter the output for a specific session (according to the socket-id) | 1..65535 |
+------------+----------------------------------------------------------------------------------+----------+

For each active session, the following information is displayed:

+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| Parameter       | Description                                                                                                  | Range                     |
+=================+==============================================================================================================+===========================+
| Session-ID      | The socket ID                                                                                                | 1..65535                  |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| User            | The gRPC user name                                                                                           | String                    |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| Uptime          | The amount of time that the session has been up                                                              | DD days, HH:MM:SS         |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| Request         | The type of session request                                                                                  | SUBSCRIBE                 |
|                 |                                                                                                              | GET                       |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| Mode            | The Subscribe Response mode.                                                                                 | STREAM                    |
|                 | gNMI allows STREAM, ONCE, POLL.                                                                              |                           |
|                 | STREAM - upon subscription, the session will remain open forever and DNOS will stream updates to the client. |                           |
|                 | POLL - the server responds with a single update message.                                                     |                           |
|                 | ONCE - the server responds with a separate update message for each path to which the client is subscribed.   |                           |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| VRF             | The type of gRPC session                                                                                     | default (in-band)         |
|                 |                                                                                                              | non-default-vrf (in-band) |
|                 |                                                                                                              | mgmt0 (out-of-band)       |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| Remote Address  | The IPv4/IPv6 address of the client that opened the gRPC session                                             | A.B.C.D:port              |
|                 |                                                                                                              | x:x::x:x:port             |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| Export Leaves   | The total number of exported telemetry updates                                                               | 64-bit counter            |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| Export Rate     | The rate of exported telemetry updates                                                                       | Mbps                      |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+
| Export LeafRate | The number of exported telemetry updates per second                                                          | Lps                       |
+-----------------+--------------------------------------------------------------------------------------------------------------+---------------------------+

**Example**
::

	dnRouter# show system grpc sessions

	| Session-ID | User  | Uptime            | Request       | Mode         | Vrf          | Remote Address | Export Leaves| Export Rate       | Export Leaf Rate |
	|------------+-------+-------------------+---------------+--------------+--------------+----------------+--------------+-------------------+------------------|
	|        776 | test  | 10 Days, 00:01:30 | SUBSCRIBE     | STREAM       | default      | 1.1.1.1:22214  |  1,221,233   | 0.6 Mbps          | 16 lps           |
	|        806 | test2 | 2 Days, 10:21:30  | SUBSCRIBE     | STREAM       | mgmt0        | 1.1.2.2:33114  |  123,222     | 0.1 Mbps          | 4 lps            |
	|        684 | test3 | 2 Days, 05:51:40  | SUBSCRIBE     | POLL         | mgmt0        | 1.2.3.4:32456  |  126,324     | 0.1 Mbps          | 8 lps            |
	|        722 | test5 | 0 Days, 0:20:01   | SUBSCRIBE     | ONCE         | mgmt0        | 1.2.3.5:34363  |  120,025     | 0.1 Mbps          | 100 lps          |
	|        752 | test4 | 0 Days, 0:20:01   | SUBSCRIBE     | POLL         | my_vrf       | 1.2.3.9:34363  |  118,025     | 0.1 Mbps          | 20 lps           |
	|        891 | test2 | 0 Days, 0:00:01   | GET           |              | mgmt0        | 1.2.3.7:32235  |              |                   |                  |

	dnRouter# show system grpc sessions 776

	| Session-ID | User  | Uptime            | Request       | Mode         | Vrf          | Remote Address | Export Leaves| Export Rate       | Export Leaf Rate |
	|------------+-------+-------------------+---------------+--------------+--------------+----------------+--------------+-------------------+------------------|
	|        776 | test  | 10 Days, 00:01:30 | SUBSCRIBE     | STREAM       | default      | 1.1.1.1:22214  |  1,221,233   | 0.6 Mbps          | 16 lps           |


	dnRouter# show system grpc sessions 777
	Error: Unknown word: '777'.


.. **Help line:** show system grpc sessions

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 11.0    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
| 13.1    | Added support for in-band (default VRF) and out-of-band (mgmt0 VRF) |
+---------+---------------------------------------------------------------------+
| 15.0    | Updated the 'Mode' parameter to support POLL and ONCE               |
+---------+---------------------------------------------------------------------+
| 16.1    | Added support for in-band (non-default VRF)                         |
+---------+---------------------------------------------------------------------+
