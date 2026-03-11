show rsvp statistics packets
----------------------------

**Minimum user role:** viewer

To display RSVP packet statistics:



**Command syntax: show rsvp statistics packet** interface [interface-name]

**Command mode:** operational



**Parameter table**

+----------------+------------------------------------------------------------------+----------------------------------------------------+
| Parameter      | Description                                                      | Range                                              |
+================+==================================================================+====================================================+
| interface-name | Filter the displayed statistics to a specific MPLS-TE interface. | ge{/10/25/40/100}-X/Y/Z                            |
|                |                                                                  |                                                    |
|                |                                                                  | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |
|                |                                                                  |                                                    |
|                |                                                                  | bundle-<bundle-id>                                 |
|                |                                                                  |                                                    |
|                |                                                                  | bundle-<bundle-id.sub-bundle-id>                   |
+----------------+------------------------------------------------------------------+----------------------------------------------------+

The following information is displayed per packet type:

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Packet    | Description                                                                                                                                 |
+===========+=============================================================================================================================================+
| Path      | Number of Path messages sent downstream or received from an upstream node.                                                                  |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| PathError | Number of Path Error messages received from a downstream neighbor or sent to an upstream neighbor.                                          |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| PathTear  | Number of Path Tear messages sent downstream, or messages received, from upstream neighbors.                                                |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Resv      | Number of reservation messages received from a downstream neighbor or sent to an upstream neighbor to reserve resources.                    |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| ResvError | Number of reservation error messages received from a upstream neighbor or sent to a downstream neighbor.                                    |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| ResvTear  | Number of reservation tear messages received from a downstream neighbor or sent to an upstream neighbor to tear down RSVP flows.            |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| SRefresh  | Number of summary refresh messages sent to and received by a neighbor to refresh the path and reservation states.                           |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Ack       | Number of acknowledgement messages sent and received by a neighbor acknowledging receipt of a message.                                      |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Nack      | If a neighboring router receives an unknown message ID in an RSVP refresh message, the router sends a Resv nack message back to the sender. |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+

The packet types are:

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Packet    | Description                                                                                                                                 |
+===========+=============================================================================================================================================+
| Path      | Number of Path messages sent downstream or received from an upstream node.                                                                  |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| PathError | Number of Path Error messages received from a downstream neighbor or sent to an upstream neighbor.                                          |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| PathTear  | Number of Path Tear messages sent downstream, or messages received, from upstream neighbors.                                                |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Resv      | Number of reservation messages received from a downstream neighbor or sent to an upstream neighbor to reserve resources.                    |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| ResvError | Number of reservation error messages received from a upstream neighbor or sent to a downstream neighbor.                                    |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| ResvTear  | Number of reservation tear messages received from a downstream neighbor or sent to an upstream neighbor to tear down RSVP flows.            |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| SRefresh  | Number of summary refresh messages sent to and received by a neighbor to refresh the path and reservation states.                           |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Ack       | Number of acknowledgement messages sent and received by a neighbor acknowledging receipt of a message.                                      |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Nack      | If a neighboring router receives an unknown message ID in an RSVP refresh message, the router sends a Resv nack message back to the sender. |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show rsvp statistics packet
	Total:
	| Packet    | Rx   | Tx   |
	|-----------+------+------|
	| Path      |    2 |    1 |
	| PathError |    0 |    0 |
	| PathTear  |    0 |    0 |
	| Resv      |    3 |    0 |
	| ResvError |    0 |    0 |
	| ResvTear  |    0 |    0 |
	| SRefresh  |    5 |    5 |
	| Ack       |    5 |    5 |
	| Nack      |    0 |    0 |

	Interface ge100-1/1/1:
	| Packet    | Rx   | Tx   |
	|-----------+------+------|
	| Path      |    0 |    0 |
	| PathError |    0 |    0 |
	| PathTear  |    0 |    0 |
	| Resv      |    0 |    0 |
	| ResvError |    0 |    0 |
	| ResvTear  |    0 |    0 |
	| SRefresh  |    0 |    0 |
	| Ack       |    0 |    0 |
	| Nack      |    0 |    0 |

	Interface bundle-2:
	| Packet    | Rx   | Tx   |
	|-----------+------+------|
	| Path      |    2 |    1 |
	| PathError |    0 |    0 |
	| PathTear  |    0 |    0 |
	| Resv      |    3 |    0 |
	| ResvError |    0 |    0 |
	| ResvTear  |    0 |    0 |
	| SRefresh  |    5 |    5 |
	| Ack       |    5 |    5 |
	| Nack      |    0 |    0 |

	dnRouter# show rsvp statistics packet interface bundle-2
	Interface bundle-2:
	Interface bundle-2:
	| Packet    | Rx   | Tx   |
	|-----------+------+------|
	| Path      |    2 |    1 |
	| PathError |    0 |    0 |
	| PathTear  |    0 |    0 |
	| Resv      |    3 |    0 |
	| ResvError |    0 |    0 |
	| ResvTear  |    0 |    0 |
	| SRefresh  |    5 |    5 |
	| Ack       |    5 |    5 |
	| Nack      |    0 |    0 |



**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
