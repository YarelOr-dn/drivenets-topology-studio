show bgp community-list
-----------------------

**Minimum user role:** viewer

To display routes matching the community-list:

**Command syntax: show bgp** {instance vrf [vrf-name]} [address-family] [sub-address-family] **community-list [community-list-name]**

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family are optional, if not specified display for all sub-address-families


**Parameter table**

+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter           | Description                                                                                                                                             | Range                       |
+=====================+=========================================================================================================================================================+=============================+
| vrf-name            | Display routing information for a non-default VRF                                                                                                       | 1..255 characters           |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family      | Display routing information for a specific address-family (AFI)                                                                                         | IPv4                        |
|                     |                                                                                                                                                         | IPv6                        |
|                     |                                                                                                                                                         | Link-state                  |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family  | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                          | unicast                     |
|                     | N/A for link-state address-family                                                                                                                       | multicast                   |
|                     |                                                                                                                                                         | vpn                         |
|                     |                                                                                                                                                         | flowspec                    |
|                     |                                                                                                                                                         | rt-constrains               |
|                     |                                                                                                                                                         | l2vpn evpn                  |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| community-list-name | Displays routes matching the community-list                                                                                                             | \-                          |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp community-list COM_LIST

	dnRouter# show bgp ipv4 community-list COM_LIST

	dnRouter# show bgp instance vrf A ipv4 community-list COM_LIST

	dnRouter# show bgp ipv6 vpn community-list COM_LIST

	dnRouter# show bgp l2vpn evpn community-list test


	BGP L2vpn EVPN, local router ID is 101.3.3.3
		Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
		Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


	Route Distinguisher: 101.1.1.1:0

	U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:21,eth-tag:=4294967295 (AD ESI)
    	     00:02:35, localpref:100 i, from: 101.1.1.1
	U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:23,eth-tag:=4294967295 (AD ESI)
    	     00:02:35, localpref:100 i, from: 101.1.1.1
	U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:21,ipv4:=101.1.1.1 (ES)
    	     00:02:35, localpref:100 i, from: 101.1.1.1
	U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:23,ipv4:=101.1.1.1 (ES)
    	     00:02:35, localpref:100 i, from: 101.1.1.1

	Route Distinguisher: 101.1.1.1:1000

	U*>i  type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=1000 (AD EVI)
         00:02:35, localpref:100 i, from: 101.1.1.1

	Route Distinguisher: 101.1.1.1:2801

	U*>i  type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=28011 (AD EVI)
    	     00:02:35, localpref:100 i, from: 101.1.1.1

    Route Distinguisher: 101.1.1.1:2802

	U*>i  type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=28021 (AD EVI)
  	       00:02:35, localpref:100 i, from: 101.1.1.1

	Route Distinguisher: 101.1.1.1:2821

	U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:21,eth-tag:=2821 (AD EVI)
    	     00:02:35, localpref:100 i, from: 101.1.1.1

	Route Distinguisher: 101.1.1.1:2823

	U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:23,eth-tag:=2823 (AD EVI)
         00:02:35, localpref:100 i, from: 101.1.1.1

	Displayed  9 out of 56 total prefixes

.. **Help line:** show bgp ipv4 routes

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
| 18.2    | Added support for l2vpn evpn SAFI                                                        |
+---------+------------------------------------------------------------------------------------------+
