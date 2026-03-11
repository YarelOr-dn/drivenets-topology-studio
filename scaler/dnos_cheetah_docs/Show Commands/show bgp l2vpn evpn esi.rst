show bgp l2vpn evpn esi
-----------------------

**Minimum user role:** viewer

To display the l2vpn EVPN BGP routing table information for a specific esi:



**Command syntax: show bgp l2vpn evpn esi**  [esi-value]

**Command mode:** operational



.. **Note**


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+
| Parameter           | Description                                                                                                                                                       | Range                                                       |
+=====================+===================================================================================================================================================================+=============================================================+
| esi-value           | The 10 byte Ethernet Segment Identifier                                                                                                                           | xx:xx:xx:xx:xx:xx:xx:xx:xx:xx                               |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+


**Example**
::

    dnRouter# show bgp l2vpn evpn esi 00:00:00:00:00:00:00:00:00:10

     BGP L2vpn EVPN, local router ID is 53.53.53.53
    Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
    Origin codes: i - IGP, e - EGP, ? - incomplete
    Next hop codes: v - Via another VRF
    RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 9999:10

    U*>   type:=1,esi:=00:00:00:00:00:00:00:00:00:10,eth-tag:=0 (AD EVI)
         05:30:28,     i, from: Local
    U* i
         14:31:35, localpref:100 i, from: 54.54.54.54

    Route Distinguisher: 53.53.53.53:0

    U*>   type:=1,esi:=00:00:00:00:00:00:00:00:00:10,eth-tag:=4294967295 (AD ESI)
         05:30:28,     i, from: Local
    U*>   type:=4,esi:=00:00:00:00:00:00:00:00:00:10,ipv4:=53.53.53.53 (ES)
         05:30:28,     i, from: Local

    Route Distinguisher: 54.54.54.54:0

    U*>i  type:=1,esi:=00:00:00:00:00:00:00:00:00:10,eth-tag:=4294967295 (AD ESI)
         14:28:49, localpref:100 i, from: 54.54.54.54
    U*>i  type:=4,esi:=00:00:00:00:00:00:00:00:00:10,ipv4:=54.54.54.54 (ES)
         14:31:50, localpref:100 i, from: 54.54.54.54

    Displayed  5 out of 18188 total prefixes

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 18.2    | Command introduced                |
+---------+-----------------------------------+
