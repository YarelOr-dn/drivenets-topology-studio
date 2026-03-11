protocols isis instance interface address-family adjacency-sid
--------------------------------------------------------------

**Minimum user role:** operator

When IS-IS forms and adjacency over a given link, it is advertised by the exteded reachability TLV. 
Segment-routing adjacency-sid allocate a specific SID , e.g label, to forward incoming matching mpls traffic over the specific adjacency. I.e to forward traffic over a specific egress interface to a known next-hop
A configured adjacency-sid will be persistent , and will hold the SID value for as long as it is configured, including system reboot. The persistent adjacency-sid is advertised with P-flag set (RFC8667)
To configure a persistent adjacency-sid:

**Command syntax: adjacency-sid [SID type] [sid-index/sid-label]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**
- Configured SID value (i.e expected label value) must be within the configured SRLB range
- Configured SID value (i.e expected label value) must be unique in the ISIS interface (due to combination of type & value)
- Configured SID value (i.e expected label value) must be unique between all ISIS interfaces and address-families
- Support up to two configured adjacency-sids per interface.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+----------------------------+---------+
| Parameter           | Description                                                                      | Range                      | Default |
+=====================+==================================================================================+============================+=========+
| SID type            | Sid type absolute or index                                                       | | index                    | \-      |
|                     |                                                                                  | | label                    |         |
+---------------------+----------------------------------------------------------------------------------+----------------------------+---------+
| sid-index/sid-label | sid-index: Assigns the prefix-SID label according to the index of the            | | sid-index: 0-31999       | \-      |
|                     | Segment-Routing Global Block used by IS-IS. The value must be within the SRGB    | | sid-label: 256-1040383   |         |
|                     | range.                                                                           |                            |         |
|                     | sid-label: Assigns the prefix-SID label as an absolute value. The value must be  |                            |         |
|                     | within the SRGB range.                                                           |                            |         |
+---------------------+----------------------------------------------------------------------------------+----------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-1
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# adjacency-sid index 10
    dnRouter(cfg-if-afi-adj-sid)#

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-1
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# adjacency-sid absolute 8001
    dnRouter(cfg-if-afi-adj-sid)#


**Removing Configuration**

To remove configured adjacency-sid:
::

    dnRouter(cfg-inst-if-afi)# no adjacency-sid absolute 8001

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
