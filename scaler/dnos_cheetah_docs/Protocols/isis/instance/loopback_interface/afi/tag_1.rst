protocols isis instance interface address-family tag level level-1
------------------------------------------------------------------

**Minimum user role:** operator

By default, no tag is set on any interface that is associated with the IS-IS instance. Use this command to associate a tag with the interface.
The tag will be attached to any prefix set on the interface for the given address-family (ipv4-unicast/ipv6-unicast), and is advertised by IS-IS.
Once tagged, the tag may subsequently match a defined policy and it may be sent in an appropriate sub-TLV (135 for IPv4 ST, 235 for IPv4 MT, 236 for IPv6 ST and 237 for IPv6 MT) when the prefix is advertised via the IS-IS protocol.

Although advertised to the rest of the world via IS-IS, the defined tag will not appear in the RIB of the local router.
The local router sees this route as a directly connected route; it does not see IS-IS as the source of this route.
Therefore, the defined tag is used only by IS-IS. This tag will not be redistributed into other protocols.

To configure the IS-IS tag per interface and address-family:

**Command syntax: tag level level-1 [tag]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**
- The tag value is signaled in the LSP as a sub-TLV of the prefix TLV.
- The tag for an IPv6 prefix can differ from the tag of an IPv4 prefix, even when working in a single-topology.
- By default the tag applies to both Levels unless the Level is explicitly indicated.
- IS-IS local interface prefix has priority over redistributed connected of the same prefix therefore the tag behavior will be in accordance with local IS-IS interface settings.

**Parameter table**

+-----------+-----------------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                           | Range        | Default |
+===========+=======================================================================+==============+=========+
| tag       | Set the tag value to be attached to prefixes and advertised by IS-IS. | 1-4294967295 | \-      |
+-----------+-----------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# tag 200

    dnRouter(cfg-protocols-isis-inst)# interface bundle-4
    dnRouter(cfg-isis-inst-if)# level level-1-2 dnRouter
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# tag level level-1 15
    dnRouter(cfg-inst-if-afi)# tag level level-2 20

    dnRouter(cfg-protocols-isis-inst)# interface bundle-5
    dnRouter(cfg-isis-inst-if)# level level-1-2
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# tag level level-1 15
    dnRouter(cfg-inst-if-afi)# tag 20


**Removing Configuration**

To remove the tag:
::

    dnRouter(cfg-inst-if-afi)# no tag level-1
    dnRouter(cfg-inst-if-afi)# no tag level-2
    dnRouter(cfg-inst-if-afi)# no tag level-2 20
    dnRouter(cfg-inst-if-afi)# no tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
