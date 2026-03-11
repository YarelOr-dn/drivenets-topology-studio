protocols bgp neighbor address-family sr-labeled-unicast allow-external-sid
---------------------------------------------------------------------------

**Minimum user role:** operator

BGP Prefix-SID Redistribution allows advertising IPv4 and IPv6 BGP Prefix-SID for SR-MPLS IPv4/IPv6-based networks. 
It is possible for BGP to carry the association of an SR-MPLS Node-SID index with an IPv4/IPv6 prefix. 
This is achieved by attaching a prefix-SID BGP path attribute containing the label-index value to an IPv4/IPv6 route belonging to either an IPv4-LU or IPv6-LU address family.
This command controls the BGP prefix-SID usage on eBGP sessions between different Autonomous Systems, as required by RFC 8669.

To enable advertisement of the local SRGB in an Originator SRGB TLV as part of the Prefix-SID attributes for locally originated routes:

**Command syntax: allow-external-sid [allow-external-sid]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family sr-labeled-unicast
- protocols bgp neighbor-group address-family sr-labeled-unicast

**Note**

- This command only supports Labeled-Unicast routes, when the Prefix-SID is enabled.

- Supported for eBGP sessions only.

- To allow usage of BGP prefix-sid on eBGP adjacencies, set the required behavior - <send-only/receive-only/send-receive/disabled>.

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter          | Description                                                                      | Range            | Default |
+====================+==================================================================================+==================+=========+
| allow-external-sid | Define exchange behaviour of Prefix-SID attribute with external peers.           | | send-only      | \-      |
|                    | Configuration only relevant for ebgp sessions                                    | | receive-only   |         |
|                    |                                                                                  | | send-receive   |         |
|                    |                                                                                  | | disabled       |         |
+--------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# sr-labeled-unicast
    dnRouter(cfg-neighbor-afi-sr-lu)# allow-external-sid send-only

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# sr-labeled-unicast
    dnRouter(cfg-group-afi-sr-lu)# allow-external-sid send-receive


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-group-afi-sr-lu)# no allow-external-sid

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
