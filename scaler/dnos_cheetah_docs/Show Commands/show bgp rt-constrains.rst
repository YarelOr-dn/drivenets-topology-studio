show bgp rt-constrains
----------------------

**Minimum user role:** viewer

To display Route Target Constrain NLRI received from BGP:

**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] rt-constrains** filter {origin-as [origin-as] | route-target [route-target]}

**Command mode:** operational


.. **Internal Note**

       - use vrf to display routing information for a non-default vrf

       - use address-family, sub-address-family for specific afi-safi routes

**Parameter table**

+----------------+-----------------------------------------------------------------+--------------------------+---------+
|    Parameter   | Description                                                     |           Range          | Default |
+================+=================================================================+==========================+=========+
| vrf-name       | Displays routing information for a non-default VRF              | 1..255 characters        | \-      |
+----------------+-----------------------------------------------------------------+--------------------------+---------+
| address-family | Display routing information for a specific address-family (AFI) | IPv4                     | \-      |
+----------------+-----------------------------------------------------------------+--------------------------+---------+
| origin-as      | Filter the displayed information by origin-AS                   | 1..4294967295 AS number  | \-      |
+----------------+-----------------------------------------------------------------+--------------------------+---------+
| route-target   | Filter the displayed information by route-target                | <as>:<id>                | \-      |
|                |                                                                 | <as>L:<id><A.B.C.D>:<id> |         |
+----------------+-----------------------------------------------------------------+--------------------------+---------+

**Example**
::

    dnRouter# show bgp ipv4 rt-constrains

	BGP IPv4 Route Target Constrains, local router ID is 100.115.115.115
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
    	          i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	    |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	U*> |4200000000:15:1000  | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:15:2000  | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:15:20001 | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:15:20002 | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:15:20003 | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:15:20004 | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:15:20005 | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:15:20006 | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:15:20007 | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:16:1000  | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:16:2000  | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:17:1000  | 0.0.0.0        |      |          |   32768|         i|
	U*> |4200000000:17:2000  | 0.0.0.0        |      |          |   32768|         i|

	Displayed  13 out of 15 total prefixes


	dnRouter# show bgp ipv4 rt-constrains filter route-target 15:20476

	BGP IPv4 Route Target Constrains, local router ID is 100.115.115.115
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
    	          i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	    |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	U*> |4200000000:15:20476 | 0.0.0.0        |      |          |   32768|         i|

	Displayed  1 out of 1 total prefixes


	dnRouter# show bgp ipv4 rt-constrains filter origin-as 4200000000


.. **Help line:** show bgp rt-constrains

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 16.1    | Command introduced                 |
+---------+------------------------------------+
