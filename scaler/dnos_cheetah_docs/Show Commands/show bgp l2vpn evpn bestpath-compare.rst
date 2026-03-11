show bgp l2vpn evpn bestpath-comare
-----------------------------------

**Minimum user role:** viewer

To display the l2vpn EVPN BGP routing table bestpath information:



**Command syntax: show bgp l2vpn evpn bestpath-compare rd [rd] nlri [nlri]**

**Command mode:** operational



.. **Note**


**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+
| Parameter           | Description                                                                                                                                                       | Range                                                       |
+=====================+===================================================================================================================================================================+=============================================================+
| route-distinguisher | Type0:                                                                                                                                                            | as-number-short: 0…(2^16 -1)                                |
|                     | <[as-number-short]:[id-long]>                                                                                                                                     | as-number-long: (2^16)…(2^32 -1)                            |
|                     | Type1:                                                                                                                                                            | id-short: 0…(2^16 -1)                                       |
|                     | <[as-number-short]l: [id-short]>                                                                                                                                  | id-long: 0…(2^32 -1)                                        |
|                     | <[as-number-short]L:[id-short]>                                                                                                                                   | ipv4-address-prefix: A.B.C.D                                |
|                     | <[as-number-long]:[id-short]>                                                                                                                                     | Note: using [as-number-short]l or [as-number-short]L will   |
|                     | Type2:                                                                                                                                                            | code as-number-short number in a 32bit                      |
|                     | <[ipv4-address-prefix>]:[id-short]>                                                                                                                               | field resulting in a Type1 route-distinguisher              |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+
| nlri                | Filter the displayed information for a specific Network Layer Reachability Information (NLRI).                                                                    | \-                                                          |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------+

**Example**
::

    dnRouter# show bgp l2vpn evpn bestpath-compare rd 101.1.1.1:0 nlri type:=1,esi:=00:11:11:11:11:11:11:11:28:21,eth-tag:=4294967295

    BGP L2vpn EVPN routing table entry for 101.1.1.1:0:type:=1,esi:=00:11:11:11:11:11:11:11:28:21,eth-tag:=4294967295 (AD ESI)
    Paths: (1 available, best #1)
        Advertised best to peers:
        101.7.7.7 101.8.8.8 101.21.21.21 101.22.22.22 101.101.101.101 102.102.102.102
      Path #1
        Local, (Received from a RR-client)
         101.1.1.1 (metric 10) from 101.1.1.1 (101.1.1.1)
        Origin IGP, localpref 100, remote-label 0, valid, internal, best
        Extended Community: RT:2821:2821 ESI-label label:118673, Single-Active
        RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
        AddPath ID: RX 0, TX 2
        Last update: 19-Jun-2023 15:43:41 UTC
        Overall best

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 18.2    | Command introduced                |
+---------+-----------------------------------+
