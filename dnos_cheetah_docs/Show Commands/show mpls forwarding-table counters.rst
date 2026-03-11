show mpls forwarding-table counters
-----------------------------------

**Minimum user role:** viewer

You can use the following command to display the global view of the MPLS forwarding table with switched-packet and switched-octet counters. The in-label displays the entries for a specific incoming label. In-lables for which counters are collected are LDP, ISIS-SR or SR-TE labels.



**Command syntax: show mpls forwarding-table counters** in-label [in-label]

**Command mode:** operational



**Note**

- In-labels, for which counters are not collected, will display the "Counters are not collected for label xxxx" message.

..
	- 'show mpls forwarding-table counters' shows the global view that includes all entries with switched packets and switched octets counters.

	- Indicating the in-label knob provides the entries for a specific incoming label. In-labels for which counters are collected are only LDP, ISIS-SR or SR-TE labels.

	- 'Egress Forwarding' may assume egress forwarding such as out interface or out policy, as applicable.

	- Only in-label in the range 16-1048575 can be indicated.

	- Indication of in-labels for which counters are not collected will display the 'Counters are not collected for label XXXX' message.

**Parameter table**

+-----------+------------------------------------------------------+-------------+---------+
| Parameter | Description                                          | Range       | Default |
+===========+======================================================+=============+=========+
| In Label  | The number of entries for a specific incoming label. | 16..1048575 | \-      |
+-----------+------------------------------------------------------+-------------+---------+

**Example**
::

	dnRouter# show mpls forwarding-table counters

	Legend: * - Active, A - Alternate path, B - Bypass
	labels are arrange from top (left) to BoS (right)

	Global MPLS Forwarding Table:
	| In Label  | Action    | Next Hop | Egress Fordwarding | Out Labels           | Switched Pkts | Switched Octets  |
	+-----------+-----------+----------+--------------------+----------------------+---------------+------------------+
	| (*)20001  | swap      | 30.1.1.2 | bundle-1           | 12345                |         34522 |     34534000     |
	| (*)       | swap      | 30.1.1.2 | bundle-2           | 10002                |         54367 |     76587634     |
	| (A)       | swap      | 30.2.2.3 | bundle-3           | 13460                |             0 |            0     |
	| (*)20002  | pop       | 30.1.1.2 | bundle-1           |                      |          9322 |      1007434     |
	| (*)2003   | swap      | 30.1.1.2 | bundle-1           | 12345                |         12543 |      4327499     |
	| (*)77534  | swap      | 30.1.1.2 | bundle-1           | 1234                 |           122 |         3434     |
	| (*)66411  | swap      | 20.2.2.3 | policy-4           | 34197, 34199         |          4322 |      1827477     |


	dnRouter# show mpls forwarding-table counters label 20001

	Legend: * - Active, A - Alternate path, B - Bypass
	labels are arrange from top (left) to BoS (right)

	Global MPLS Forwarding Table:
	| In Label  | Action    | Next Hop | Egress Forwarding | Out Labels           | Switched Pkts | Switched Octets  |
	+-----------+-----------+----------+-------------------+----------------------+---------------+------------------+
	| (*)20001  | swap      | 30.1.1.2 | bundle-1          | 12345                |         34522 |     34534000     |
	| (*)       | swap      | 30.1.1.2 | bundle-2          | 10002                |         54367 |     76587634     |
	| (A)       | swap      | 30.2.2.3 | bundle-3          | 13460                |             0 |            0     |


	dnRouter# show mpls forwarding-table counters label 340000

	Counters are not collected for label 340000

.. **Help line:** Displays global MPLS forwarding table entries with counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+


