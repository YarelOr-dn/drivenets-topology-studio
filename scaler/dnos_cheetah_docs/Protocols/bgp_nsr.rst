protocols bgp nsr
-----------------

**Minimum user role:** operator

BGP nonstop routing (NSR) enables a BGP speaker to maintain the BGP session's state while undergoing switchover at the CPU level (e.g. NCC switchover).
Unlike BGP graceful-restart (GR), which requires both BGP ends to support the GR capability and logic, NSR is transparent, and the other end of the BGP session is unaware of the NSR process.
BGP NSR provides a high availability (HA) solution where the neighbor router does not support BGP GR.

The BGP process (bgpd) running on the active NCC, saves all the information required to recover from a BGP failure and provide nonstop routing (including BGP session information for both iBGP and eBGP neighbors, and TCP session information) in the NSR DB (including all BGP acknowledged and unacknowledged packets).
The NSR DBs, located on both active and standby NCC, are regularly synchronized. In the event of a switchover/failover, bgpd starts on the standby NCC and recovers the TCP and BGP session parameters from the NSR-DB in the standby NCC.
BGP NSR does not require the neighbor router to be NSF-capable or NSF-aware, however, it relies on the "route-refresh" capability in order to re-converge after the BGP process recovers.

BGP NSR is applicable to the following address families:

* IPv4-unicast, IPv6-unicast
* IPv4-labeled-unicast, IPv6-labeled-unicast
* IPv4-vpn, IPv6-vpn
* IPv4-rt-constrains
* IPv4-multicast

BGP NSR is supported only on NCEs with external NCCs (i.e. cluster topology).

To enable/disable the BGP NSR feature:

**Command syntax: bgp nsr [nsr]**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- This is a global BGP configuration that applies to all BGP instances and VRFs.

**Parameter table**

+-----------+---------------------+--------------+---------+
| Parameter | Description         | Range        | Default |
+===========+=====================+==============+=========+
| nsr       | bgp nsr admin-state | | enabled    | enabled |
|           |                     | | disabled   |         |
+-----------+---------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp nsr enabled

    dnRouter(cfg-protocols)# bgp nsr disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols)# no bgp nsr

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 13.0    | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 16.1    | Changed hierarchy for the command to apply to all BGP instances |
+---------+-----------------------------------------------------------------+
