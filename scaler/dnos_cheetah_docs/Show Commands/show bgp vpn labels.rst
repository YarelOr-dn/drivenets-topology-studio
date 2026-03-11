show bgp vpn labels
-------------------

**Minimum user role:** viewer

To display the BGP VPN label for prefixes (use rd to display related routes that are used in a specific vrf):

**Command syntax: show bgp [address-family] vpn labels** rd [route-distinuisher]

**Command mode:** operational

.. **Note:**

**Parameter table:**

+----------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+---------+
|       Parameter      | Description                                           |                                                                      Range                                                                     | Default |
+======================+=======================================================+================================================================================================================================================+=========+
| address-family       | Display BGP label for a specific address-family (AFI) | IPv4                                                                                                                                           | \-      |
|                      |                                                       | IPV6                                                                                                                                           |         |
+----------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| route-distinghuisher | Type0:                                                | as-number-short: 1..(2^16 -1)                                                                                                                  | \-      |
|                      |                                                       |                                                                                                                                                |         |
|                      | <[as-number-short]:[id-long]>                         | as-number-long: (2^16).(2^32 -1)                                                                                                               |         |
|                      |                                                       |                                                                                                                                                |         |
|                      | Type2:                                                | id-short: 1..(2^16 -1)                                                                                                                         |         |
|                      |                                                       |                                                                                                                                                |         |
|                      | <[as-number-short]l: [id-short]>                      | id-long: 1..(2^32 -1)                                                                                                                          |         |
|                      |                                                       |                                                                                                                                                |         |
|                      | <[as-number-short]L:[id-short]>                       | ipv4-address-prefix: A.B.C.D                                                                                                                   |         |
|                      |                                                       |                                                                                                                                                |         |
|                      | <[as-number-long]:[id-short]>                         | Note: using [as-number-short]l or [as-number-short]L will code as-number-short number in a 32bit field resulting in a Type1 route-distinguishe |         |
|                      |                                                       |                                                                                                                                                |         |
|                      | Type1:                                                |                                                                                                                                                |         |
|                      |                                                       |                                                                                                                                                |         |
|                      | <[ipv4-address-prefix>:[id-short]>                    |                                                                                                                                                |         |
+----------------------+-------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Example**
::

	dnRouter# show bgp ipv4 vpn labels

    BGP IPv4 Vpn, local router ID is 100.116.116.116
    Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  - multipath, a - alternate-path,
                i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
    Origin codes: i - IGP, e - EGP, ? - incomplete
    Next hop codes: v - Via another VRF
    RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 100.14.14.14:1601

    |       Network          | Lb. In/Lb. out |    Next hop    |Metric|  LocPref | Weight |   Path   |
    ------------------------------------------------------------------------------------------------------
    U*> |16.14.100.0/32      |  177250/1040395| 100.114.114.114|      |          |       0|7018 1461 i|
    U*> |16.14.100.1/32      |  177249/1040395| 100.114.114.114|      |          |       0|7018 1461 i|

    Route Distinguisher: 100.15.15.15:1601

       |       Network      | Lb. In/Lb. out      |    Next hop    |Metric|  LocPref | Weight |   Path   |
    -------------------------------------------------------------------------------------------------------
    *> |3.0.0.0/8           |       118670/1040577 | 10.0.2.3       |     0|          |       0|       2 i|
    *> |22.22.2.0/24        |       118668/1040577 | 173.0.25.2     |     0|          |       0|       2 i|

    Route Distinguisher: 100.18.18.18:1601

       |       Network      | Lb. In/Lb. out      |    Next hop    |Metric|  LocPref | Weight |   Path   |
    -------------------------------------------------------------------------------------------------------
    *> |4.0.0.0/8           |       nolabel/118669 | 10.0.3.3       |     0|          |       0|       2 i|


	dnRouter# show bgp ipv6 vpn labels

    BGP IPv6 Vpn, local router ID is 100.116.116.116
    Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
                i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
    Origin codes: i - IGP, e - EGP, ? - incomplete
    Next hop codes: v - Via another VRF
    RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 100.14.14.14:1601

    |                   Network                  | Lb. In/Lb. out |                Next hop                |Metric|  LocPref | Weight |   Path   |
    --------------------------------------------------------------------------------------------------------------------------------------------------
    U*> |2016:14:100::/128                           |  176751/1040395| ::ffff:100.114.114.114                 |      |          |       0|7018 1461 i|
    U*> |2016:14:100::1/128                          |  176750/1040395| ::ffff:100.114.114.114                 |      |          |       0|7018 1461 i|
    U*> |2016:14:100::2/128                          |  176749/1040395| ::ffff:100.114.114.114                 |      |          |       0|7018 1461 i|
    U*> |2016:14:100::3/128                          |  176748/1040395| ::ffff:100.114.114.114                 |      |          |       0|7018 1461 i|


    dnRouter# show bgp ipv6 vpn labels rd 100.14.14.14:1601

    BGP IPv6 Vpn, local router ID is 100.116.116.116
    Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, =  -multipath, a - alternate-path,
                i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
    Origin codes: i - IGP, e - EGP, ? - incomplete
    Next hop codes: v - Via another VRF
    RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified


    Route Distinguisher: 100.14.14.14:1601

    |                   Network                  | Lb. In/Lb. out |                Next hop                |Metric|  LocPref | Weight |   Path   |
    --------------------------------------------------------------------------------------------------------------------------------------------------
    U*> |2016:14:100::/128                           |  176751/1040395| ::ffff:100.114.114.114                 |      |          |       0|7018 1461 i|
    U*> |2016:14:100::1/128                          |  176750/1040395| ::ffff:100.114.114.114                 |      |          |       0|7018 1461 i|
    U*> |2016:14:100::2/128                          |  176749/1040395| ::ffff:100.114.114.114                 |      |          |       0|7018 1461 i|

.. **Help line:** Display BGP vpn label for prefixes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
