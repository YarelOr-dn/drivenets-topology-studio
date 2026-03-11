show bfd summary
----------------

**Minimum user role:** viewer

To display summary information of BFD sessions:



**Command syntax: show bfd summary**

**Command mode:** operational



**Example**
::

	dnRouter# show bfd summary

	| Clients           | Num sessions   | Up   | Down   | Init   | Admin-Down   |
	|-------------------+----------------+------+--------+--------+--------------|
	| Interface-Manager | 7              | 7    | 0      | 0      | 0            |
	| RSVP              | 0              | 0    | 0      | 0      | 0            |
	| BGP               | 404            | 387  | 16     | 0      | 1            |
	| OSPF              | 215            | 215  | 0      | 0      | 0            |
	| OSPFv3            | 0              | 0    | 0      | 0      | 0            |
	| Static            | 0              | 0    | 0      | 0      | 0            |
	| IS-IS             | 0              | 0    | 0      | 0      | 0            |
	| Segment-Routing   | 18             | 18   | 0      | 0      | 0            |

	| BFD type     | Num sessions   | Up   | Down   | Init   | Admin-Down   |
	|--------------+----------------+------+--------+--------+--------------|
	| Micro BFD    | 7              | 7    | 0      | 0      | 0            |
	| MPLS         | 0              | 0    | 0      | 0      | 0            |
	| Multi-hop    | 4              | 3    | 0      | 0      | 1            |
	| Single-hop   | 615            | 599  | 16     | 0      | 0            |
	| Seamless BFD | 18             | 18   | 0      | 0      | 0            |
	Total number of sessions: 644
	Maximum sessions limit: 2000

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 11.2    | Command introduced                |
+---------+-----------------------------------+
| 11.6    | Added support for OSPF and OSPFv3 |
+---------+-----------------------------------+
| 12.0    | Added support for BFD for IS-IS   |
+---------+-----------------------------------+
| 18.3    | Added support for Seamless BFD    |
+---------+-----------------------------------+
| 19      | Display maximum sessions limit    |
+---------+-----------------------------------+
