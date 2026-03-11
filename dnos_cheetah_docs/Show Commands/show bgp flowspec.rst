show bgp flowspec
-----------------

**Minimum user role:** viewer

To display FlowSpec NLRI received from BGP:


**Command syntax: show bgp** instance vrf [vrf-name] **[address-family] flowspec** {nlri [nlri] | destination [dest-prefix] source [src-prefix]}

**Command mode:** operational


..
       **Internal Note**

       - use vrf to display routing information for a non-default vrf

       - use address-family, sub-address-family for specific afi-safi routes

       - nlri - require to use apostrophes when entring the nlri string

**Parameter table**

+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter        | Description                                                                                                                                                       | Range                       |
+==================+===================================================================================================================================================================+=============================+
| vrf-name         | Display routing information for a non-default VRF                                                                                                                 | 1..255 characters           |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family   | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                        |
|                  |                                                                                                                                                                   | IPv6                        |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| nlri             | Filter the displayed information for a specific Network Layer Reachability Information (NLRI).                                                                    | \-                          |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| dest-prefix      | Filters the displayed NLRI by the incoming traffic's destination prefix.                                                                                          | A.B.C.D/M                   |
|                  | The destination prefix must match the address-family.                                                                                                             | xx:xx::xx:xx/O-M            |
|                  |                                                                                                                                                                   | M - The prefix mask length. |
|                  |                                                                                                                                                                   | O - The ipv6 offset         |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| src-prefix       | Filters the displayed NLRI by the incoming traffic's source prefix.                                                                                               | A.B.C.D/M                   |
|                  | The source prefix must match the address-family.                                                                                                                  | xx:xx::xx:xx/O-M            |
|                  |                                                                                                                                                                   | M - The prefix mask length. |
|                  |                                                                                                                                                                   | O - The ipv6 offset         |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

       dnRouter# show bgp ipv4 flowspec nlri "DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5"

       DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
         1
       0.0.0.0 from 192.168.1.2 (9.9.9.2)
       Origin IGP, metric 0, localpref 100, valid, external, best
       Extended Community: flowspec-redirect-ip-nh:0 flowspec-traffic-rate:1:500
       AddPath ID: RX 0, TX 2
       Last update: Thu Nov  7 14:38:37 2019


       dnRouter# show bgp ipv4 flowspec destination 50.0.0.0/8

       DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
         1
       0.0.0.0 from 192.168.1.2 (9.9.9.2)
       Origin IGP, metric 0, localpref 100, valid, external, best
       Extended Community: flowspec-redirect-ip-nh:0 flowspec-traffic-rate:1:500
       AddPath ID: RX 0, TX 2
       Last update: Thu Nov  7 14:38:37 2019

       dnRouter# show bgp ipv4 flowspec destination 50.0.0.0/8 source 50.1.2.3/32

       DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
         1
       0.0.0.0 from 192.168.1.2 (9.9.9.2)
       Origin IGP, metric 0, localpref 100, valid, external, best
       Extended Community: flowspec-redirect-ip-nh:0 flowspec-traffic-rate:1:500
       AddPath ID: RX 0, TX 2
       Last update: Thu Nov  7 14:38:37 2019

       dnRouter# show bgp ipv6 flowspec destination 2::/64-128

       DstPrefix:=*,SrcPrefix:=2001:7:7:7::3/128
         7922
       from 4.4.0.198 (4.4.4.4)
       Origin incomplete, localpref 100, valid, external, best
       Extended Community: flowspec-traffic-rate:0:0
       AddPath ID: RX 0, TX 2
       Last update: Mon Jun 15 15:34:56 2020

.. **Help line:** show bgp flowspec nlri

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 13.0    | Command introduced                 |
+---------+------------------------------------+

