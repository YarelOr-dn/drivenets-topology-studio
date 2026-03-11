show bgp community
------------------

**Minimum user role:** viewer

To display routes matching the community attribute:

**Command syntax: show bgp** {instance vrf [vrf-name]} [address-family] [sub-address-family] **community** [community] [community] [community] [community]

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family and community are optional, if not specified display for all sub-address-families and communities

	- community can be set up to 4 times in order to include several communities

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
| community          | Displays routes matching the communities attribute. This can be added up to four times within the command to include several communities. Values:       |                             |
|                    | no-export: Routes received with this community value MUST NOT be advertised outside of the AS.                                                          |                             |
|                    | no-advertise:Routes received with this community value MUST NOT be advertised to neighbors.                                                             |                             |
|                    | local-as:Must not be sent outside local AS.AA: 1-65534 NN: 0-65535                                                                                      |                             |
|                    | <AA:NN>:                                                                                                                                                | \-                          |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp community

	dnRouter# show bgp ipv4 community 5:5000

	BGP VPN-IPv4 Unicast table , local router ID is 100.70.1.45
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	Route Distinguisher: 10.173.1.66:30

	   Network          Next Hop           Metric LocPrf Weight Path
	*>i20.0.0.0/24      7.7.7.7                        0      0 i
	*>i20.0.1.0/24      7.7.7.7                        0      0 i
	*>i20.0.2.0/24      7.7.7.7                        0      0 i
	*>i20.0.3.0/24      7.7.7.7                        0      0 i
	*>i20.0.4.0/24      7.7.7.7                        0      0 i

	dnRouter# show bgp ipv4 community 5:5000

	BGP VPN-IPv4 Unicast table , local router ID is 100.70.1.45
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	Route Distinguisher: 10.173.1.66:30

	   Network          Next Hop           Metric LocPrf Weight Path
	*> 10.173.1.64/30   0.0.0.0 v               0         32768 ?
	*> 11.0.0.0/24      10.173.1.66 v                         0 5001 i
	*> 11.0.1.0/24      10.173.1.66 v                         0 5001 i
	*> 11.0.2.0/24      10.173.1.66 v                         0 5001 i
	*> 11.0.3.0/24      10.173.1.66 v                         0 5001 i
	*> 11.0.4.0/24      10.173.1.66 v                         0 5001 i

	dnRouter# show bgp ipv4 vpn community local-as

	BGP VPN-IPv4 Unicast table , local router ID is 100.70.1.45
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified

	Route Distinguisher: 10.173.1.66:30

	   Network          Next Hop           Metric LocPrf Weight Path
	*>i20.0.0.0/24      7.7.7.7                        0      0 i
	*>i20.0.1.0/24      7.7.7.7                        0      0 i
	*>i20.0.2.0/24      7.7.7.7                        0      0 i
	*>i20.0.3.0/24      7.7.7.7                        0      0 i
	*>i20.0.4.0/24      7.7.7.7                        0      0 i

	dnRouter# show bgp ipv4 vpn community local-as no-export 50:50

	dnRouter# show bgp instance vrf A ipv4 unicast community local-as

	dnRouter# show bgp l2vpn evpn community 222:222

        BGP L2vpn EVPN, local router ID is 101.3.3.3
        Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
        Origin codes: i - IGP, e - EGP, ? - incomplete
        Next hop codes: v - Via another VRF
        RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 101.1.1.1:0

    U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:21,eth-tag:=4294967295 (AD ESI)
         00:00:42, localpref:100 i, from: 101.1.1.1
    U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:23,eth-tag:=4294967295 (AD ESI)
         00:00:42, localpref:100 i, from: 101.1.1.1
    U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:21,ipv4:=101.1.1.1 (ES)
         00:00:42, localpref:100 i, from: 101.1.1.1
    U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:23,ipv4:=101.1.1.1 (ES)
         00:00:42, localpref:100 i, from: 101.1.1.1

    Route Distinguisher: 101.1.1.1:1000

    U*>i  type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=1000 (AD EVI)
         00:00:42, localpref:100 i, from: 101.1.1.1

    Displayed  9 out of 56 total prefixes

.. **Help line:** displays routes matching the community attribute

**Command History**

+---------+------------------------------------------------------------------------------------------+
| Release | Modification                                                                             |
+=========+==========================================================================================+
| 6.0     | Command introduced                                                                       |
+---------+------------------------------------------------------------------------------------------+
| 16.1    | Added support for link-state AFI and both flowspec and IPv4 Route Target Constrain SAFIs |
+---------+------------------------------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI                                                    |
+---------+------------------------------------------------------------------------------------------+
| 18.2    | Added support for L2VPN EVPN SAFI                                                        |
+---------+------------------------------------------------------------------------------------------+