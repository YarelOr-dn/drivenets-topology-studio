show rsvp statistics errors
---------------------------

**Minimum user role:** viewer

To display protocol errors statistics per error type:



**Command syntax: show rsvp statistics errors** interface [interface-name]

**Command mode:** operational




**Parameter table**

+----------------+----------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Parameter      | Description                                                                                                    | Range                                              |
+================+================================================================================================================+====================================================+
| interface-name | Filters the displayed errors statistics to the specified interface. Applies to a configured MPLS-TE interface. | ge{/10/25/40/100}-X/Y/Z                            |
|                |                                                                                                                |                                                    |
|                |                                                                                                                | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |
|                |                                                                                                                |                                                    |
|                |                                                                                                                | bundle-<bundle-id>                                 |
|                |                                                                                                                |                                                    |
|                |                                                                                                                | bundle-<bundle-id.sub-bundle-id>                   |
+----------------+----------------------------------------------------------------------------------------------------------------+----------------------------------------------------+

The error types are:

+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Event                                | Description                                                                                                                            |
+======================================+========================================================================================================================================+
| Packet parsing failure               | Failed to parse received packet, for example due to bad length, unknown type, bad version, bad checksum, bad format, bad lsp-id format |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Receive packet on disabled interface | Number of RSVP packets received on an interface that is not enabled for RSVP.                                                          |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| No path information                  | A reservation was received, but no sender is active.                                                                                   |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Unknown LSP                          | Received packet (by type) with unknown LSP identifier                                                                                  |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Path timeout                         | Number of times the sender timed out because the path was removed.                                                                     |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Resv timeout                         | Number of times the receiver timed out because the reservation was removed.                                                            |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| CAC failures                         | CAC could no allocate bandwidth in cac due to insufficant bandwidth                                                                    |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| CSPF failures                        | CSPF could not find a path                                                                                                             |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| LSP Preemption                       | Number of preemption events on local node                                                                                              |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Label allocation failures            | Could not allocate a label for a required tunnel                                                                                       |
+--------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show rsvp statistics errors
	Total:

	| Error type                           | Total   |
	|--------------------------------------+---------|
	| Packet parsing failure               |       0 |
	| Receive packet on disabled interface |       0 |
	| Unknown LSP                          |       1 |
	| Path timeout                         |       0 |
	| Resv timeout                         |       1 |
	| CAC failures                         |       0 |
	| CSPF failures                        |       0 |
	| LSP Preemption                       |       3 |
	| Label allocation failures            |       0 |

	Interface ge100-1/1/1:
	| Error type             | Total   |
	|------------------------+---------|
	| Packet parsing failure |       0 |
	| Message out-of-order   |       0 |
	| No path information    |       0 |
	| Unknown LSP            |       0 |
	| Path timeout           |       0 |
	| Resv timeout           |       0 |

	Interface bundle-2:
	| Error type             | Total   |
	|------------------------+---------|
	| Packet parsing failure |       0 |
	| Message out-of-order   |       0 |
	| No path information    |       0 |
	| Unknown LSP            |       1 |
	| Path timeout           |       0 |
	| Resv timeout           |       1 |

	dnRouter# show rsvp statistics errors interface bundle-2
	Interface bundle-2:
	| Error type             | Total   |
	|------------------------+---------|
	| Packet parsing failure |       0 |
	| Message out-of-order   |       0 |
	| No path information    |       0 |
	| Unknown LSP            |       1 |
	| Path timeout           |       0 |
	| Resv timeout           |       1 |



**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
