show bgp memory
---------------

**Minimum user role:** viewer

Display global BGP memory statistics:


**Command syntax: show bgp memory**

**Command mode:** operational

.. **Note**


.. **Parameter table**

**Example**
::

	dnRouter# show bgp memory

	9249536 RIB nodes, using > 2GB of memory
	4623655 BGP routes, using 564 MiB of memory
	4622740 BGP route ancillaries, using 141 MiB of memory
	2271143 Adj-In entries, using 121 MiB of memory
	4771166 Adj-Out entries, using > 2GB of memory
	1978 Nexthop cache entries, using 6799 KiB of memory
	6034 BGP attributes, using 424 KiB of memory
	6034 BGP extra attributes, using 754 KiB of memory
	2 unknown attributes
	906 BGP AS-PATH entries, using 35 KiB of memory
	905 BGP AS-PATH segments, using 21 KiB of memory
	9 BGP community entries, using 360 bytes of memory
	4575 BGP ecommunity entries, using 179 KiB of memory
	1 Cluster lists, using 32 bytes of memory
	2909 peers, using 394 MiB of memory
	9 peer groups, using 432 bytes of memory
	906 RT nodes, using 609 KiB of memory
	906 RD nodes, using 14 KiB of memory
	46559 hash tables, using 1819 KiB of memory
	19767 hash buckets, using 463 KiB of memory
	

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+

