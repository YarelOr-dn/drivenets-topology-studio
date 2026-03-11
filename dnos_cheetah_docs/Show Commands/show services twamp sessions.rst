show services twamp sessions
----------------------------

**Minimum user role:** viewer

This command displays the data and control connection type and identifiers, local (source interface) and remote (destination) IP and communication ports, and the received and transmitted packet statistics on each of the connections. TWAMP can support up to ten simultaneous control sessions, which can be from the same client or different clients. Each control session can support up to ten simultaneous data sessions. This means that in total there can be up to 100 simultaneous data sessions.

To display the active TWAMP sessions in the system:

**Command syntax: show services twamp sessions** type [type] vrf [vrf-name] connection-id [connection-id] session-id [session-id] local-address [local-address] remote-address [remote-address]

**Command mode:** operational



..
	**Internal Note**

	- Rx and Tx counters counts the number of packets per session, counters are reset once session is reset


**Example**
::

	dnRouter# show services twamp sessions

	TWAMP Sessions:

	| VRF      | Connection-ID | Session-ID | Type    | Local Address | Remote Address | Session Uptime  | RX[pkts] | TX[pkts] |
	|----------+---------------+------------+---------+---------------+----------------+-----------------+----------+----------|
	| default  | 100           |            | control | 1.2.3.4:1000  | 1.1.1.1:862    | 1 day, 01:01:05 | 123      | 345      |
	| default  | 100           | 806        | data    | 1.2.3.4:3311  | 1.1.1.1:2211   | 1 day, 01:01:05 | 123      | 345      |
	| default  | 100           | 807        | data    | 1.2.3.4:3312  | 1.1.1.1:2212   | 1 day, 01:01:05 | 123      | 345      |

	Total displayed connections: 1
	Total displayed sessions: 2


	dnRouter# show services twamp sessions session-id 806

	TWAMP Sessions:

	| VRF      | Connection-ID | Session-ID | Type    | Local Address | Remote Address | Session Uptime  | RX[pkts] | TX[pkts] |
	|----------+---------------+------------+---------+---------------+----------------+-----------------+----------+----------|
	| default  | 100           | 806        | data    | 1.2.3.4:3311  | 1.1.1.1:2211   | 1 day, 01:01:05 | 123      | 345      |

	Total displayed connections: 1
	Total displayed sessions: 1


.. **Help line:** Displays active TWAMP sessions in system

**Command History**

+---------+------------------------------------------+
| Release | Modification                             |
+=========+==========================================+
| 11.2    | Command introduced                       |
+---------+------------------------------------------+
| 16.2    | Added VRF column and output filters      |
+---------+------------------------------------------+
