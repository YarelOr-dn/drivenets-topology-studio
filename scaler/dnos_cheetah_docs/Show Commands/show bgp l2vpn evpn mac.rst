show bgp l2vpn evpn mac
-----------------------

**Minimum user role:** viewer

To display the l2vpn EVPN BGP routing table information:



**Command syntax: show bgp l2vpn evpn mac**  [mac-address]

**Command mode:** operational



.. **Note**


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+
| Parameter           | Description                                                                                                                                                       | Range                                                       |
+=====================+===================================================================================================================================================================+=============================================================+
| mac-address         | The mac-address                                                                                                                                                   | xx:xx:xx:xx:xx:xx                                           |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+


**Example**
::


   dnRouter# show bgp l2vpn evpn mac 00:10:53:54:11:03


    BGP L2vpn EVPN, local router ID is 53.53.53.53
    Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
    Origin codes: i - IGP, e - EGP, ? - incomplete
    Next hop codes: v - Via another VRF
    RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 54:1

    U*>i  type:=2,eth-tag:=0,mac-address:=00:10:53:54:11:03  (MAC)
         00:28:03, localpref:100 i, from: 54.54.54.54

    Displayed  1 out of 5976 total prefixes

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 18.2    | Command introduced                |
+---------+-----------------------------------+
