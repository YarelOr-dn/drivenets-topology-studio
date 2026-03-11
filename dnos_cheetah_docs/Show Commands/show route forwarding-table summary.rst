show route forwarding-table summary
-----------------------------------

**Minimum user role:** viewer

To display a summary of all routes on the forwarding table, use the following command:

**Command syntax: show route forwarding-table summary** { vrf [vrf-name] | all } { ncp [ncp-id] | all }

**Command mode:** operational


**Note**

- By default, the information is displayed for the default VRF only. When 'all' is specified, a summary for all configured VRFs is displayed.

.. - default route calculated inside "route" row. If NCP is disconnecetd or not reachable, output will show "NCP x not connected"

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------+--------------+------------------------+
| Parameter | Description                                                                               | Range        | Default                |
+===========+===========================================================================================+==============+========================+
| vrf-name  | Optionally filters the displayed information to a specific VRF.                           | String | all | default                |
+-----------+-------------------------------------------------------------------------------------------+--------------+------------------------+
| ncp-id    | Optionally filters the displayed information to a specific NCP.                           | 0..255 | all | NCP with the lowest ID |
|           | If the NCP is disconnected or unreachable, the output will display "NCP x not connected". |              |                        |
+-----------+-------------------------------------------------------------------------------------------+--------------+------------------------+
| all       | Displays the forwarding table for all NCPs.                                               | \-           | \-                     |
+-----------+-------------------------------------------------------------------------------------------+--------------+------------------------+

The following information is displayed:

+---------------------+-----------------------------------------------------------------+-----------+
| Parameter           | Description                                                     | Range     |
+=====================+=================================================================+===========+
| Type                | The type of routes for which the number of entries is displayed | Route     |
|                     |                                                                 | Local     |
|                     |                                                                 | Connected |
|                     |                                                                 | Discard   |
+---------------------+-----------------------------------------------------------------+-----------+
| IPv4 Entries        | The number of IPv4 routes per route type                        | Integer   |
+---------------------+-----------------------------------------------------------------+-----------+
| IPv6 Entries        | The number of IPv6 routes per route type                        | Integer   |
+---------------------+-----------------------------------------------------------------+-----------+
| MPLS entries        | The total number of MPLS routes                                 | Integer   |
+---------------------+-----------------------------------------------------------------+-----------+
| Nexthop elements    | The total number of next-hops                                   | Integer   |
+---------------------+-----------------------------------------------------------------+-----------+
| ECMP nexthop groups | The total number of equal-cost multi-path next-hop groups       | Integer   |
+---------------------+-----------------------------------------------------------------+-----------+
| ARP entries         | The total number of ARP entries                                 | Integer   |
+---------------------+-----------------------------------------------------------------+-----------+
| MAC entries         | The total number of MAC entries                                 | Integer   |
+---------------------+-----------------------------------------------------------------+-----------+


**Example**
::




	dnRouter# show route forwarding-table summary

    NCP-ID: 0
    | Type      | IPv4 Entries   | IPv6 Entries   |
    |-----------+----------------+----------------|
    | discard   | 0              | 0              |
    | local     | 783            | 1397           |
    | connected | 954            | 939            |
    | route     | 1313798        | 309711         |
    | Total     | 1315535        | 312047         |

    MPLS entries: 11136
    ARP entries: 1265
    MAC entries: 1763

    Nexthop elements:
    1st:       12108/314572
    2nd:       1/183502
    3rd:       12487/157286
    protected: 82/65536
    ECMP:      2716/38911

    warning threshold: 75%


    dnRouter# show route forwarding-table summary vrf default

    VRF: default
    NCP-ID: 0
    | Type      | IPv4 Entries   | IPv6 Entries   |
    |-----------+----------------+----------------|
    | discard   | 0              | 0              |
    | local     | 167            | 164            |
    | connected | 225            | 201            |
    | route     | 1012517        | 8729           |
    | Total     | 1012909        | 9094           |


    dnRouter# show route forwarding-table summary ncp 0

    NCP-ID: 0
    | Type      | IPv4 Entries   | IPv6 Entries   |
    |-----------+----------------+----------------|
    | discard   | 0              | 0              |
    | local     | 783            | 1397           |
    | connected | 955            | 931            |
    | route     | 1314017        | 110229         |
    | Total     | 1315755        | 112557         |

    MPLS entries: 11133
    ARP entries: 1284
    MAC entries: 1763

    Nexthop elements:
    1st:       12107/314572
    2nd:       1/183502
    3rd:       12480/157286
    protected: 81/65536
    ECMP:      2716/38911

    warning threshold: 75%


	dnRouter# show route forwarding-table summary ncp 3
	ERROR: No information found.

	dnRouter# show route forwarding-table summary ncp all
	NCP-ID: 0
	| Type      | IPv4 Entries   | IPv6 Entries   |
    |-----------+----------------+----------------|
    | discard   | 0              | 0              |
    | local     | 783            | 1397           |
    | connected | 955            | 931            |
    | route     | 1315967        | 110229         |
    | Total     | 1317705        | 112557         |

    MPLS entries: 11133
    ARP entries: 1284
    MAC entries: 1867

    Nexthop elements:
    1st:       12107/314572
    2nd:       1/183502
    3rd:       12480/157286
    protected: 81/65536
    ECMP:      2716/38911

    warning threshold: 75%

	NCP 1 not connected

	NCP-ID: 2

	| Type      | IPv4 Entries   | IPv6 Entries   |
	|-----------+----------------+----------------|
	| discard   | 0              | 0              |
	| local     | 783            | 1397           |
	| connected | 955            | 931            |
	| route     | 1315967        | 110229         |
	| Total     | 1317705        | 112557         |

    MPLS entries: 11133
    ARP entries: 1284
	MAC entries: 14238

    Nexthop elements:
    1st:       12107/314572
    2nd:       1/183502
    3rd:       12480/157286
    protected: 81/65536
    ECMP:      2716/38911

    warning threshold: 75%


	dnRouter# show route forwarding-table summary vrf all ncp 1
	dnRouter# show route forwarding-table summary vrf all ncp all

.. **Help line:** show route forwarding-table summary


**Command History**

+---------+-----------------------------+
| Release | Modification                |
+=========+=============================+
| 5.1.0   | Command introduced          |
+---------+-----------------------------+
| 11.0    | Added ncp-id filter         |
+---------+-----------------------------+
| 13.0    | Added all to command syntax |
+---------+-----------------------------+
| 17.2    | Added MAC entries           |
+---------+-----------------------------+
