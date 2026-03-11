show bgp unicast labels
-----------------------

**Minimum user role:** viewer

To display BGP label for prefixes:

**Command syntax: show bgp [address-family] unicast labels** route [ip-prefix] in-label [out-label] out-label [out-label]

**Command mode:** operational



.. **Note**


**Parameter table**

+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter        | Description                                                                                                                                                       | Range                       |
+==================+===================================================================================================================================================================+=============================+
| address-family   | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                        |
|                  |                                                                                                                                                                   | IPv6                        |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| ip-prefix        | IP-prefix in IPv4 format or IPv6 format. Must match the AFI or SAFI when specified.                                                                               | A.B.C.D/x                   |
|                  |                                                                                                                                                                   | xx:xx::xx:xx/x              |
+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| in-label         | Displays only in-labels                                                                                                                                           | 0..1048575, no label        |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| out-label        | Displays only out-labels                                                                                                                                          | 0..1048575, no label        |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

  dnRouter# show bgp ipv4 unicast labels

  BGP IPv4 Unicast, local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified
    
       |       Network      | Lb. In/Lb. out |    Next hop    |Metric|  LocPref | Weight |   Path   |
    ---------------------------------------------------------------------------------------------------
    *> |2.0.0.0/8           |        118669/3| 10.0.1.3       |     0|          |       0|       2 i|
    *> |3.0.0.0/8           |   118670/118668| 10.0.2.3       |     0|          |       0|       2 i|
    *> |4.0.0.0/8           |  nolabel/118669| 10.0.3.3       |     0|          |       0|       2 i|
    *> |22.22.2.0/24        |        118668/3| 173.0.25.2     |     0|          |       0|       2 i|
    *a |                    |       nolabel/3| 173.0.25.3     |      |          |       0|     3 2 i|


  dnRouter# show bgp ipv6 unicast labels
  
  BGP IPv6 Unicast, local router ID is 9.9.9.2
	Status codes: s - suppressed, d - damped, h - history, * - valid, > - best, = - multipath, a - alternate-path,
	              i - internal, r - RIB-failure, S - Stale, SL - LLGR Stale, R - Removed, L - over-limit, x - best-external
	Origin codes: i - IGP, e - EGP, ? - incomplete
	Next hop codes: v - Via another VRF
	RPKI validation codes: V - valid, I - invalid, N - not-found, U - unverified
    
       |                   Network                  | Lb. In/Lb. out |                Next hop                |Metric|  LocPref | Weight |   Path   |
    -----------------------------------------------------------------------------------------------------------------------------------------------------
    *> |1230::2/128                                 |        118668/2| 3450::11                               |     0|          |       0|       3 i|
    *> |1232::2/128                                 |   118670/118668| 3451::11                               |     0|          |       0|       3 i|
    *> |1233::2/128                                 |  nolabel/118669| 3452::11                               |     0|          |       0|       3 i|


.. **Help line:**

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 6.0     | Command introduced                            |
+---------+-----------------------------------------------+
| 11.0    | Added ip-prefix and in/out-label filters      |
+---------+-----------------------------------------------+
| 15.0    | Added support to display IPv6 labeled-unicast |
+---------+-----------------------------------------------+

