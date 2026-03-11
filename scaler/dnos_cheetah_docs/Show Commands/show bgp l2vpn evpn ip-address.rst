show bgp l2vpn evpn ip-address
------------------------------

**Minimum user role:** viewer

To display the l2vpn EVPN BGP routing table information:



**Command syntax: show bgp l2vpn evpn ip-address**  [ip-address]

**Command mode:** operational



.. **Note**


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+
| Parameter           | Description                                                                                                                                                       | Range                                                       |
+=====================+===================================================================================================================================================================+=============================================================+
| ip-address          | Either an IPv4 or an IPv6 address                                                                                                                                 |  A.B.C.D / X:X::X:X                                         |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+


**Example**
::

    dnRouter# show bgp l2vpn evpn eth-tag 2823

    dnRouter# show bgp l2vpn evpn ip-address 101.1.1.1


    BGP L2vpn EVPN, local router ID is 101.3.3.3
    Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
    Origin codes: i - IGP, e - EGP, ? - incomplete
    Next hop codes: v - Via another VRF
    RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 101.1.1.1:0

    U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:21,ipv4:=101.1.1.1 (ES)
         01:22:10, localpref:100 i, from: 101.1.1.1
    U*>i  type:=4,esi:=00:11:11:11:11:11:11:11:28:23,ipv4:=101.1.1.1 (ES)
         01:22:10, localpref:100 i, from: 101.1.1.1

    Displayed  2 out of 56 total prefixes

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 18.2    | Command introduced                |
+---------+-----------------------------------+
