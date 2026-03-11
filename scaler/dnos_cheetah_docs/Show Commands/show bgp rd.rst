show bgp rd
-----------

**Minimum user role:** viewer

Display information for a route distinguisher:

**Command syntax: show bgp [address-family] [sub-address-family] rd [route-distinuisher]** {ip-address [ip-address] \| ip-prefix [ip-prefix] \| tags }

**Command mode:** operational


..
	**Internal Note**

	- ip-address/prefix - route in the bgp routing table to display

	- tags - display bgp tags for prefixes

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter           | Description                                                                                                                                                       | Range                                                                                                                                           |
+=====================+===================================================================================================================================================================+=================================================================================================================================================+
| address-family      | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                                                                                                                                            |
|                     |                                                                                                                                                                   | IPv6                                                                                                                                            |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| sub-address-family  | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                                    | unicast                                                                                                                                         |
|                     | N/A for link-state address-family                                                                                                                                 | multicast                                                                                                                                       |
|                     |                                                                                                                                                                   | l2vpn evpn                                                                                                                                      |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| ip-address          | IP address in IPv4 format  or IPv6 format. Must match the AFI or SAFI when specified.                                                                             | A.B.C.D                                                                                                                                         |
|                     |                                                                                                                                                                   | xx:xx::xx:xx                                                                                                                                    |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| ip-prefix           | IP-prefix in IPv4 format or IPv6 format. Must match the AFI or SAFI when specified.                                                                               | A.B.C.D/x                                                                                                                                       |
|                     |                                                                                                                                                                   | xx:xx::xx:xx/x                                                                                                                                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| route-distinguisher | Type0:                                                                                                                                                            | as-number-short: 0…(2^16 -1)                                                                                                                    |
|                     | <[as-number-short]:[id-long]>                                                                                                                                     | as-number-long: (2^16)…(2^32 -1)                                                                                                                |
|                     | Type1:                                                                                                                                                            | id-short: 0…(2^16 -1)                                                                                                                           |
|                     | <[as-number-short]l: [id-short]>                                                                                                                                  | id-long: 0…(2^32 -1)                                                                                                                            |
|                     | <[as-number-short]L:[id-short]>                                                                                                                                   | ipv4-address-prefix: A.B.C.D                                                                                                                    |
|                     | <[as-number-long]:[id-short]>                                                                                                                                     | Note: using [as-number-short]l or [as-number-short]L will code as-number-short number in a 32bit field resulting in a Type1 route-distinguisher |
|                     | Type2:                                                                                                                                                            |                                                                                                                                                 |
|                     | <[ipv4-address-prefix>]:[id-short]>                                                                                                                               |                                                                                                                                                 |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| tags                | Displays BGP tags for the prefixes                                                                                                                                | \-                                                                                                                                              |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show bgp ipv4 vpn rd 50:50

	dnRouter# show bgp ipv4 vpn rd 50:1.1.1.1 ip-prefix 2.2.0.0/16

	dnRouter# show bgp ipv4 vpn rd 50:1.1.1.1 tags

	dnRouter# show bgp ipv6 vpn rd 100L:50 ip-address 2:2::2:2

   
    dnRouter# show bgp l2vpn evpn rd 101.1.1.1:2801

	BGP L2vpn EVPN, local router ID is 101.3.3.3
		Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
		Origin codes: i - IGP, e - EGP, ? - incomplete
		Next hop codes: v - Via another VRF
		RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


		Route Distinguisher: 101.1.1.1:2801

		U*>i  type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=28011 (AD EVI)
        	 00:06:00, localpref:100 i, from: 101.1.1.1

		Displayed  1 out of 1 total prefixes


.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 6.0     | Command introduced                |
+---------+-----------------------------------+
| 18.2    | Added support for L2VPN EVPN SAFI |
+---------+-----------------------------------+