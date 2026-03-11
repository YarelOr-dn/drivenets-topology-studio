show bgp nexthop
----------------

**Minimum user role:** viewer

To display BGP nexthop table:


**Command syntax: show bgp** instance vrf [vrf-name] **nexthop** [routing-table] {ip-address [ip-address] \| reachable \| unreachable }

**Command mode:** operational


..
    **Internal Note**

    - reachable - Reachable nexthops

    - unreachable - Unreachable nexthops

**Parameter table**

+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter        | Description                                                                                                                                                       | Range                       |
+==================+===================================================================================================================================================================+=============================+
| vrf-name         | Display routing information for a non-default VRF                                                                                                                 | 1..255 characters           |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| routing-table    | Display routing information for the specified routing table                                                                                                       | unicast-rib                 |
|                  |                                                                                                                                                                   | multicast-rib               |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| ip-address       | IP address in IPv4 format  or IPv6 format. Must match the AFI or SAFI when specified.                                                                             | A.B.C.D                     |
|                  |                                                                                                                                                                   | xx:xx::xx:xx                |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| reachable        | Reachable nexthop                                                                                                                                                 |                             |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| unreachable      | Unreachable nexthop                                                                                                                                               |                             |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

 dnRouter# show bgp nexthop

 Table: Unicast RIB
 ------------------

 Current BGP nexthop cache:
 4.4.0.21/32 valid (isis) [IGP metric 10], #paths 3489974
  gate 2.2.2.2, if bundle-1921, resolved by: 4.4.0.21/32
  gate 101.19.63.1, if bundle-80.203, resolved by: 4.4.0.21/32
  MPLS reachability: no, Connected: no
  Last update: Wed Jul 22 07:29:00 2020
  NextHop Trigger Delay: 5sec

 4.4.0.63/32 valid (isis) [IGP metric 10], #paths 150000
  gate 101.19.63.1, if bundle-80.203, resolved by: 4.4.0.63/32
  gate 2.2.2.2, if bundle-1921, resolved by: 4.4.0.63/32
  MPLS reachability: no, Connected: no
  Last update: Wed Jul 22 08:01:18 2020
  NextHop Trigger Delay: 5sec

 5.5.5.5/32 valid (bgp) [IGP metric 0], #paths 1997
  gate 172.16.1.1, if bundle-401.3533, resolved by: 0.0.0.0/0
  gate 172.16.4.1, if bundle-402.3539, resolved by: 0.0.0.0/0
  gate 172.16.8.1, if bundle-404.3547, resolved by: 0.0.0.0/0
  gate 172.16.2.1, if bundle-401.3535, resolved by: 0.0.0.0/0
  gate 172.16.3.1, if bundle-402.3537, resolved by: 0.0.0.0/0
  gate 172.16.7.1, if bundle-404.3545, resolved by: 0.0.0.0/0
  gate 172.16.6.1, if bundle-403.3543, resolved by: 0.0.0.0/0
  gate 172.16.5.1, if bundle-403.3541, resolved by: 0.0.0.0/0
  gate 2.2.2.2, if bundle-1921, resolved by: 0.0.0.0/0
  gate 101.19.63.1, if bundle-80.203, resolved by: 0.0.0.0/0
  MPLS reachability: no, Connected: no
  Last update: Wed Jul 22 08:11:20 2020
  NextHop Trigger Delay: 5sec
  Invalid for:
   Address-family IPv4 Unicast due to next-hop-tracking policy NEXT-HOP-TRACKING

 56.33.44.0/32 valid (connected) [IGP metric 0], #paths 2
  if ge100-2/0/6, resolved by: 56.33.44.0/31
  MPLS reachability: no, Connected: yes
  Last update: Tue Jul 21 16:04:10 2020
  NextHop Trigger Delay: 5sec remaining 2sec

 69.20.50.1/32 valid (connected) [IGP metric 0], #paths 5450
  if bundle-1.2000, resolved by: 69.20.50.0/31
  MPLS reachability: no, Connected: yes
  Last update: Wed Jul 22 08:07:57 2020
  NextHop Trigger Delay: 5sec remaining 2sec

 69.20.50.3/32 valid (connected) [IGP metric 0], #paths 5450
  if bundle-1.2001, resolved by: 69.20.50.2/31
  MPLS reachability: no, Connected: yes
  Last update: Wed Jul 22 08:07:48 2020
  NextHop Trigger Delay: 5sec remaining 2sec

 Table: Multicast RIB
 --------------------

 Current BGP nexthop cache:
 4.4.0.21/32 valid (isis) [IGP metric 10], #paths 3489974
  gate 2.2.2.2, if bundle-1921, resolved by: 4.4.0.21/32
  gate 101.19.63.1, if bundle-80.203, resolved by: 4.4.0.21/32
  MPLS reachability: no, Connected: no
  Last update: Wed Jul 22 07:29:00 2020
  NextHop Trigger Delay: 5sec


 dnRouter# show bgp nexthop unicast-rib ip-address 4.4.0.63

 4.4.0.63/32 valid (isis) [IGP metric 10], #paths 150000
  gate 101.19.63.1, if bundle-80.203, resolved by: 4.4.0.63/32
  gate 2.2.2.2, if bundle-1921, resolved by: 4.4.0.63/32
  MPLS reachability: no, Connected: no
  Last update: Wed Jul 22 08:01:19 2020
  NextHop Trigger Delay: 5sec

 dnRouter# sysp19(27-Feb-2020-07:31:09)# show bgp nexthop unicast-rib reachable

 Current BGP nexthop cache:
 4.4.0.21/32 valid (isis) [IGP metric 10], #paths 3521436
  gate 2.2.2.2, if bundle-1921, resolved by: 4.4.0.21/32
  gate 101.19.63.1, if bundle-80.203, resolved by: 4.4.0.21/32
  MPLS reachability: no, Connected: no
  Last update: Wed Jul 22 07:29:01 2020
  NextHop Trigger Delay: 5sec

 4.4.0.63/32 valid (isis) [IGP metric 10], #paths 150000
  gate 101.19.63.1, if bundle-80.203, resolved by: 4.4.0.63/32
  gate 2.2.2.2, if bundle-1921, resolved by: 4.4.0.63/32
  MPLS reachability: no, Connected: no
  Last update: Wed Jul 22 08:01:19 2020
  NextHop Trigger Delay: 5sec

 5.5.5.5/32 valid (bgp) [IGP metric 0], #paths 1997
  gate 172.16.1.1, if bundle-401.3533, resolved by: 0.0.0.0/0
  gate 172.16.4.1, if bundle-402.3539, resolved by: 0.0.0.0/0
  gate 172.16.8.1, if bundle-404.3547, resolved by: 0.0.0.0/0
  gate 172.16.2.1, if bundle-401.3535, resolved by: 0.0.0.0/0
  gate 172.16.3.1, if bundle-402.3537, resolved by: 0.0.0.0/0
  gate 172.16.7.1, if bundle-404.3545, resolved by: 0.0.0.0/0
  gate 172.16.6.1, if bundle-403.3543, resolved by: 0.0.0.0/0
  gate 172.16.5.1, if bundle-403.3541, resolved by: 0.0.0.0/0
  gate 2.2.2.2, if bundle-1921, resolved by: 0.0.0.0/0
  gate 101.19.63.1, if bundle-80.203, resolved by: 0.0.0.0/0
  MPLS reachability: no, Connected: no
  Last update: Wed Jul 22 08:11:21 2020
  NextHop Trigger Delay: 5sec
  Invalid for:
   Address-family IPv4 Unicast due to next-hop-tracking policy NEXT-HOP-TRACKING


 56.33.44.0/32 valid (connected) [IGP metric 0], #paths 2
  if ge100-2/0/6, resolved by: 56.33.44.0/31
  MPLS reachability: no, Connected: yes
  Last update: Tue Jul 21 16:04:11 2020
  NextHop Trigger Delay: 5sec


 dnRouter# show bgp nexthop multicast-rib unreachable

  Current BGP nexthop cache:
  Peer 1.8.19.0 bfd nexthop cache:
  nht: su_local 1.8.19.1, nht: interface: bundle-819.819, ifindex 14829, Last update: Wed Feb 26 17:56:38 2020

.. **Help line:**

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 6.0     | Command introduced                               |
+---------+--------------------------------------------------+
| 13.0    | Added display of invalid nexthop tracking policy |
+---------+--------------------------------------------------+
| 16.1    | Added support for MRIB table                     |
+---------+--------------------------------------------------+
