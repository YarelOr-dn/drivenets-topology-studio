protocols bgp address-family ipv4-unicast bgp-leak import-from policy
---------------------------------------------------------------------

**Minimum user role:** operator

BGP route leaking between vrfs is used to have routes learned an one vrf (including default) and to be used and advertised to peers in another vrf.
BGP route leaking is based on routes being copied between the bgp vrf table and is not subject to l3vpn import/export logic.
A leak policy must be specified
Up to 4 leak imports can be set in a given vrf.

**Command syntax: bgp-leak import-from [origin-vrf] policy [policy-name]** [, policy-name, policy-name]

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast
- network-services vrf instance protocols bgp address-family ipv6-unicast

**Note**

- Up to 4 different VRFs can used as source VRFs for leaking into the single destination VRF

- A leaked route cannot be leaked again, meaning a route with the "leak-origin" attribute will not be leaked

- A leaked route can be exported to vpn safi, meaning a route that was leaked from vrf A to vrf B and exported from vrf B.

- A vpn route that was leaked, cannot be imported to the same vrf as origin. The route that was leaked from vrf A to vrf B and exported from vrf B, cannot not be importet back to vrf A from vpn.

- An imported route cannot be leaked. If it is required to have the imported route in destination vrf, import to that vrf.

**Parameter table**

+-------------+--------------------------------+------------------+---------+
| Parameter   | Description                    | Range            | Default |
+=============+================================+==================+=========+
| origin-vrf  | origin-vrf                     | | string         | \-      |
|             |                                | | length 1-255   |         |
+-------------+--------------------------------+------------------+---------+
| policy-name | impose policy on leaked routes | | string         | \-      |
|             |                                | | length 1-255   |         |
+-------------+--------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# bgp-leak import-from VRF_A policy LEAK_FROM_A1, LEAK_FROM_A2

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf
    dnRouter(cfg-netsrv-vrf)# instance A
    dnRouter(cfg-netsrv-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# bgp 1
    dnRouter(cfg-vrf-inst-protocols)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# bgp-leak import-from default policy LEAK_FROM_DEFAULT1, LEAK_FROM_DEFAULT2


**Removing Configuration**

To stop all leakage:
::

    dnRouter(cfg-protocols-bgp-afi)# no bgp-leak import-from

To stop leakage from a specific vrf:
::

    dnRouter(cfg-protocols-bgp-afi)# no bgp-leak import-from VRF_A

To remove policy from a specific vrf:
::

    dnRouter(cfg-protocols-bgp-afi)# no bgp-leak import-from VRF_A policy LEAK_FROM_A1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
