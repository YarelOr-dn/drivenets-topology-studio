show bgp color
------------------

**Minimum user role:** viewer

To display routes matching the color extended community attribute:

**Command syntax: show bgp** instance vrf [vrf-name] [address-family] [sub-address-family] **color [color]** [color] [color] [color]

**Command mode:** operational


..
	**Internal Note**

	- instance address-family and sub-address-family are optional, if not specified display for all sub-address-families and default vrf

	- color can be set up to 4 times in order to include several colors

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                             | Range                       |
+====================+=========================================================================================================================================================+=============================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                       | 1..255 characters           |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                         | IPv4                        |
|                    |                                                                                                                                                         | IPv6                        |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                          | unicast                     |
|                    | N/A for link-state address-family                                                                                                                       | vpn                         |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| color              | Displays routes matching the color extended community attribute. This can be added up to four times within the command to include several colors.       | 0..4294967295               |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp ipv4 color 5

	BGP IPv4 Unicast, local router ID is 9.9.9.4
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
	            i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	    |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	U*> |1.0.0.0/8           | 10.0.2.2       |      |          |       0|       1 i|
	U*> |2.0.0.0/8           | 10.0.2.2       |     0|          |       0|       1 i|

	dnRouter# show bgp vrf default color 3

	BGP IPv4 Unicast, local router ID is 9.9.9.4
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
	            i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	    |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	U*> |1.0.0.0/8           | 10.0.2.2       |      |          |       0|       1 i|

.. **Help line:** displays routes matching the color extended community attribute

**Command History**

+---------+------------------------------------------------------------------------------------------+
| Release | Modification                                                                             |
+=========+==========================================================================================+
| 17.0    | Command introduced                                                                       |
+---------+------------------------------------------------------------------------------------------+
