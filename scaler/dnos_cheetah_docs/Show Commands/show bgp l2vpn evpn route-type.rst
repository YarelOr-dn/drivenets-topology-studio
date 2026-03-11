show bgp l2vpn evpn route-type
------------------------------

**Minimum user role:** viewer

To display the l2vpn EVPN BGP routing table information for a specific route-type:



**Command syntax: show bgp l2vpn evpn route-type**  [route-type-number]

**Command mode:** operational



.. **Note**


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+
| Parameter           | Description                                                                                                                                                       | Range                                                       |
+=====================+===================================================================================================================================================================+=============================================================+
| route-type-number   | The route-type number                                                                                                                                             | value between 1 and 4                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+


**Example**
::


    dnRouter# show bgp l2vpn evpn route-type 4


    BGP L2vpn EVPN, local router ID is 53.53.53.53
    Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
    Origin codes: i - IGP, e - EGP, ? - incomplete
    Next hop codes: v - Via another VRF
    RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 52.52.52.52:0

    U*>i  type:=4,esi:=00:00:22:33:44:55:66:77:88:00,ipv4:=52.52.52.52 (ES)
         13:42:26, localpref:100 i, from: 52.52.52.52
    U*>i  type:=4,esi:=00:11:22:33:44:55:66:77:88:97,ipv4:=52.52.52.52 (ES)
         13:42:26, localpref:100 i, from: 52.52.52.52
    U*>i  type:=4,esi:=00:11:22:33:44:55:66:77:88:99,ipv4:=52.52.52.52 (ES)
         13:42:26, localpref:100 i, from: 52.52.52.52

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 18.2    | Command introduced                |
+---------+-----------------------------------+
