show bgp l2vpn evpn eth-tag
---------------------------

**Minimum user role:** viewer

To display the l2vpn EVPN BGP routing table information for a specific ethernet tag:



**Command syntax: show bgp l2vpn evpn eth-tag**  [vlan-id]

**Command mode:** operational



.. **Note**


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+
| Parameter           | Description                                                                                                                                                       | Range                                                       |
+=====================+===================================================================================================================================================================+=============================================================+
| vlan-id             | The vlan-id value.                                                                                                                                                | 0..4094                                                     |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+


**Example**
::

    dnRouter# show bgp l2vpn evpn eth-tag 2823


    BGP L2vpn EVPN, local router ID is 101.3.3.3
    Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
    Origin codes: i - IGP, e - EGP, ? - incomplete
    Next hop codes: v - Via another VRF
    RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 101.1.1.1:2823

    U*>i  type:=1,esi:=00:11:11:11:11:11:11:11:28:23,eth-tag:=2823 (AD EVI)
         00:04:24, localpref:100 i, from: 101.1.1.1

    Displayed  1 out of 56 total prefixes

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 18.2    | Command introduced                |
+---------+-----------------------------------+
