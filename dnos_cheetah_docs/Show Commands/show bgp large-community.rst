show bgp large-community
------------------------

**Minimum user role:** viewer


**Command syntax: show bgp** {instance vrf [vrf-name] [address-family]} [sub-address-family] **large-community** [large-community] [large-community] [large-community] [large-community]

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family and community are optional, if not specified display for all sub-address-families and communities

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                             | Range                       |
+====================+=========================================================================================================================================================+=============================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                       | 1..255 characters           |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                         | IPv4                        |
|                    |                                                                                                                                                         | IPv6                        |
|                    |                                                                                                                                                         | Link-state                  |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                          | unicast                     |
|                    | N/A for link-state address-family                                                                                                                       | multicast                   |
|                    |                                                                                                                                                         | vpn                         |
|                    |                                                                                                                                                         | flowspec                    |
|                    |                                                                                                                                                         | rt-constrains               |
|                    |                                                                                                                                                         | l2vpn evpn                  | 
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| large-community    | Displays routes matching the large-communities attribute. This can be added up to four times within the command to include several communities. Values: | AS_number: 0..4294967295    |
|                    | <AS_number:id-1:id-2>                                                                                                                                   | id-1: 0..4294967295         |
|                    |                                                                                                                                                         | id-2: 0..4294967295         |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp large-community 42000134:5:5000

	BGP IPv4 Unicast, local router ID is 100.112.112.112
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	   |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	*> |5.12.0.0/32         | 5.12.90.1      |      |          |       0|    7018 i|
	*> |5.12.0.1/32         | 5.12.90.1      |      |          |       0|    7018 i|
	*> |5.12.0.2/32         | 5.12.90.1      |      |          |       0|    7018 i|
	*> |5.12.0.3/32         | 5.12.90.1      |      |          |       0|    7018 i|


	dnRouter# show bgp large-community 42000134:5:5000 42000134:5:6000

	BGP IPv4 Unicast, local router ID is 100.112.112.112
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	   |       Network      |    Next hop    |Metric|  LocPref | Weight |   Path   |
	-----------------------------------------------------------------------------------
	*> |5.12.0.0/32         | 5.12.90.1      |      |          |       0|    7018 i|



	dnRouter# show bgp l2vpn evpn large-community 123:456:789

	BGP L2vpn EVPN, local router ID is 101.3.3.3
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


	Route Distinguisher: 101.1.1.1:0

	U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:21,eth-tag:=4294967295 (AD ESI)
         00:00:57, localpref:100 i, from: 101.1.1.1
	U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:23,eth-tag:=4294967295 (AD ESI)
         00:00:57, localpref:100 i, from: 101.1.1.1
	U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:21,ipv4:=101.1.1.1 (ES)
         00:00:57, localpref:100 i, from: 101.1.1.1
	U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:23,ipv4:=101.1.1.1 (ES)
         00:00:57, localpref:100 i, from: 101.1.1.1


    Displayed  4 out of 56 total prefixes

.. **Help line:** displays routes matching the large community attribute


**Command History**

+---------+------------------------------------------------------------------------------------------+
| Release | Modification                                                                             |
+=========+==========================================================================================+
| 15.1    | Command introduced                                                                       |
+---------+------------------------------------------------------------------------------------------+
| 16.1    | Added support for link-state AFI and both flowspec and IPv4 Route Target Constrain SAFIs |
+---------+------------------------------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI                                                    |
+---------+------------------------------------------------------------------------------------------+
