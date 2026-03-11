show bgp l2vpn evpn all nlri
--------------------------------

**Minimum user role:** viewer

To display a network in the BGP routing table:



**Command syntax: show bgp l2vpn evpn all nlri [nlri]**

**Command mode:** operational



.. **Note**


**Parameter table**

+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter        | Description                                                                                                                                                       | Range                       |
+==================+===================================================================================================================================================================+=============================+
| nlri             | Filter the displayed information for a specific Network Layer Reachability Information (NLRI).                                                                    | \-                          |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

    dnRouter# show bgp l2vpn evpn all nlri type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=2113

    BGP L2vpn EVPN routing table entry for 65000:2113:type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=2113 (AD EVI)
    Paths: (1 available, best #1)
    Advertised best to peers:
    101.1.1.1 101.7.7.7 101.8.8.8 101.21.21.21 101.22.22.22 101.101.101.101 102.102.102.102
    Path #1
      Local
          :: [evi PE7-test_100]   from Local (101.3.3.3)
        Origin IGP, localpref 100, local-label 118700, weight 32768, valid, best
        Extended Community: RT:65000:2113 EVPN-Layer-2-attr mtu:1999 control-word flow-label
        RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
        AddPath ID: RX 0, TX 2
        Last update: 19-Jun-2023 15:43:38 UTC

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 18.2    | Command introduced                |
+---------+-----------------------------------+
