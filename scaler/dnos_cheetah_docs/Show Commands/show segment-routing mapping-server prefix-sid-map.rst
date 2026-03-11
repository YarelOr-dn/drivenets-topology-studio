show segment-routing mapping-server prefix-sid-map:
---------------------------------------------------

**Minimum user role:** viewer

To display the locally configured prefix to SID mapping:

**Command syntax: show segment-routing mapping-server prefix-sid-map**

**Command mode:** operational



**Parameter table**

+-----------+-----------------------------------------------------------+
| Parameter | Description                                               |
+===========+===========================================================+
| Prefix    | The prefix for which the SID is mapped.                   |
+-----------+-----------------------------------------------------------+
| SID Index | The SID index mapped to the prefix                        |
+-----------+-----------------------------------------------------------+
| Range     | The number of automatically allocated SIDs for the prefix |
+-----------+-----------------------------------------------------------+
| Flags     | The associated flag                                       |
+-----------+-----------------------------------------------------------+

**Example**
::

	dnRouter# show segment-routing mapping-server prefix-sid-map

	Preferece: 128

	| Prefix     	 | SID Index     | Range       | Last Prefix    | Flags |
	+----------------+---------------+-------------+----------------+-------+
	| 101.0.0.1/32   | 4001          | 100         | 101.0.0.100/32 |       |
	| 101.0.2.1/32   | 7001          | 5           | 101.0.2.5/32   | S     |
	| 101.0.3.1/32   | 7031          | 1           | 101.0.3.1/32   |       |

	Total mapping entries: 3

.. **Help line:** Display the locally configured prefix to sid maps

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+


