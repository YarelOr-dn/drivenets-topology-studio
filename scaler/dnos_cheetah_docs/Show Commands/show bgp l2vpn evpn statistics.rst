show bgp l2vpn evpn statistics
------------------------------

**Minimum user role:** viewer

To display the l2vpn EVPN BGP RIB statistics:



**Command syntax: show bgp l2vpn evpn statistics**

**Command mode:** operational



.. **Note**



**Example**
::

    dnRouter# show bgp l2vpn evpn statistics

    VRF default:
    BGP L2vpn EVPN RIB statistics

    Total Prefixes with path      :        16203
    Total paths                   :        18188
    Average prefix length         :         0.00
    Unaggregateable prefixes      :        16203
    Maximum aggregateable prefixes:            0
    BGP Aggregate advertisements  :            0
    Address space advertised      :            0

    Total paths with AS-Path      :        18188
    Longest AS-Path (hops)        :            1
    Average AS-Path length (hops) :         0.00
    Largest AS-Path (bytes)       :            6
    Average AS-Path size (bytes)  :         0.01
    Highest public ASN            :         7015

.. **Help line:**

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 18.2    | Command introduced                |
+---------+-----------------------------------+
