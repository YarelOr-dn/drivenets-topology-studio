show msdp peers
---------------

**Minimum user role:** viewer

You can use this command to display information of MSDP peers.

**Command syntax: show msdp peers** [peer-address]

**Command mode:** operational



**Note**

- The peers are sorted by Mesh Group and not by Per IP address.

- Applies only if the peer-address displays the detailed information of the specified peer.

..
	- Providing the peer-address displays the detailed information of the specified peer

	- The peers are sorted by Mesh Group and then by Peer IP address

**Parameter table**

+--------------+---------------------------------------------------------+---------+---------+
| Parameter    | Description                                             | Range   | Default |
+==============+=========================================================+=========+=========+
| peer-address | Filters the displayed information to the specified peer | A.B.C.D | None    |
+--------------+---------------------------------------------------------+---------+---------+

The following information is displayed for the MSDP peers:

+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter         | Description                                                                                                                                                                           |
+===================+=======================================================================================================================================================================================+
| Peer address      | Peer IPv4 address                                                                                                                                                                     |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Admin state       | MSDP connection administrative state Enabled/Disabled                                                                                                                                 |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Connection State  | MSDP connection session state Established/Listen/Connecting/Inactive                                                                                                                  |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Uptime/Downtime   | MSDP connection Uptime/Downtime                                                                                                                                                       |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Local Source IP   | MSDP connection source IP                                                                                                                                                             |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Accepted SA       | The number of unique MSDP SA states that were accepted from this peer and cached, i.e. after filtering.                                                                               |
|                   | if the same SA was accepted from a different peer after it was accepted from this peer, the Accepted SA counter in this peer will be decreased.                                       |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Received SA       | All non unique MSDP SAs that were received from this peer, including refreshed SA replications of the same SA state                                                                   |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Peer/Mesh group   | The Mesh Group name the specific peer belongs to or (default peer) indication if not a mesh group member                                                                              |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Last Reset Reason | One of the following Peering session reset reasons: invalid-state / connect-failed / tlv-tx-failed / invalid-tlv-rx / peer-down / hold-timer-expired source-update / clear-msdp-peers |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show msdp peers

	Legend: l - MSDP SA loop detected

	MSDP Peers:
	+---------------------+-------------+------------------+-----------------+-------------+---------------+--------------------+----------+
	| Peer Address        | Admin State | Connection State | Uptime/Downtime | Received SA | Accepted SA   | Peer/Mesh group    | Peer AS  |
	+=====================+=============+==================+=================+=============+===============+====================+==========+
	| 1.2.3.4             | Enabled     | Established      |       00:00:23  |      12342  |          823  | US_MeshGRoup       |     234  |
	| 3.3.3.3             | Enabled     | Established (l)  |       00:12:23  |         23  |           23  | US_MeshGRoup       |     234  |
	| 8.8.8.8             | Enabled     | Established      |       00:12:23  |        500  |          489  | US_MeshGRoup       |     234  |
	| 23.23.1.2           | Enabled     | Listen           |       01:13:45  |          0  |            0  | US_MeshGRoup       |     234  |
	| 1.4.4.4             | Disabled    | Inactive         |       00:00:00  |          0  |            0  | (default peer)     |    2345  |
	| 7.7.7.7             | Enabled     | Established      |       00:10:23  |      18002  |        18002  | (default peer)     |       4  |
	| 8.8.8.8             | Enabled     | Established      |       00:45:21  |       1700  |         1700  | (default peer)     |      23  |
	| 9.9.9.9             | Enabled     | Established      |       00:12:23  |        342  |            0  | (default peer)     |      42  |
	+---------------------+-------------+------------------+-----------------+-------------+---------------+--------------------+----------+

	dnRouter# show msdp peers 3.3.3.3

	MSDP Peer: 3.3.3.3
		Admin state         :  Enabled
		Local source IP		:  1.1.1.1
		Peer AS         	:  234
		Mesh Group / Peer	:  US_MeshGRoup
		Connection State	:  Established (loop detected)
		Uptime / Downtime	:  00:12:23
		Keepalive Timer		:  00:00:42/00:01:00
		Conn Retry Timer	:  --:--:--
		Hold Timer  		:  00:01:08/00:01:20
		Last Reset Reason	:  invalid-tlv-rx
		Received SAs		:  53
		Accepted SAs		:  23
		Connection Attempts	:   7
		Established Changes	:   1
		Peer timeouts 		:  12
		MSDP TLV counters   :
			+--------------+-------------+-------------+
			| MSDP TLVs    |   Sent      |  Received   |
			+--------------+-------------+-------------+
			| Keepalives   |        1    |     2       |
			| SAs          |        2    |     8       |
			+--------------+-------------+-------------+
		MSDP TLV Errors    :
			+--------------+-------------+
			| MSDP Errors  |  Received   |
			+--------------+-------------+
			| Unknown TLVs |        0    |
			| Error TLVs   |       10    |
			+--------------+-------------+


.. **Help line:** Show MSDP peers

**Command History**

+---------+--------------------------------------------------------------------------------+
| Release | Modification                                                                   |
+=========+================================================================================+
| 12.0    | Command introduced                                                             |
+---------+--------------------------------------------------------------------------------+
| 16.1    | Added admin-state per peer and a flag to indicate detection of aמ MSDP SA loop |
+---------+--------------------------------------------------------------------------------+

