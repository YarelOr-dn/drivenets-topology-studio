show bgp neighbor bmp
---------------------

**Minimum user role:** viewer

The following command displays detailed BMP information per BGP neighbor.

**Command syntax: show bgp** instance vrf [vrf-name] **neighbors** [neighbor-address] **bmp**

**Command mode:** operational


..
	**Internal Note**

	- support auto-complete for configured server-id


**Parameter table**

+------------------+---------------------------------------------------+-------------------+
| Parameter        | Description                                       | Range             |
+==================+===================================================+===================+
| vrf-name         | Display routing information for a non-default VRF | 1..255 characters |
+------------------+---------------------------------------------------+-------------------+
| neighbor-address | Neighbor address                                  | A.B.C.D           |
|                  |                                                   | xx:xx::xx:xx      |
+------------------+---------------------------------------------------+-------------------+

**Example**
::

	dnRouter# show bgp neighbor bmp

	Neighbor 3.3.3.3:

		Active BMP server:
		| ID    | Peer-Up    | Peer-Down   | Route-Monitoring  |
		|-------+------------+-------------+-------------------+
		| 0     |         12 |           0 |              15   |
		| 2     |          0 |           0 |               0   |
		| 4     |          0 |           0 |               0   |

		Exported BGP tables:
			IPv4-Unicast
				adj-in pre-policy
				adj-in post-policy
			IPv6-Unicast
				adj-in pre-policy
				adj-in post-policy

		Neighbor 4.4.4.4:

		Active BMP server:
		| ID    | Peer-Up    | Peer-Down   | Route-Monitoring  |
		|-------+------------+-------------+-------------------+
		| 0     |         2  |           1 |               3   |
		| 2     |          0 |           0 |               0   |

		Exported BGP tables:
			IPv4-Unicast
				adj-in pre-policy
				adj-in post-policy
			IPv6-Unicast
				adj-in post-policy

.. **Help line:** displays detailed bmp session information

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+

