protocols segment-routing mpls mapping-server prefix-sid-map
------------------------------------------------------------

**Minimum user role:** operator

To configure a prefix to SID mapping. This mapping is advertised as a binding-SID when the router acts as a mapping server.

To configure a prefix to SID mapping:

**Command syntax: prefix-sid-map [prefix-sid-mapping] [start-sid]** range [range] s-flag [s-flag]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls mapping-server

**Note**
- Require commit validation that all prefix-sid are in the SRGB range

- Require commit validation that mapping policy doesn't include overlapping prefixes that assigned different labels. e.g

  - 20.1.1.0/24 16000 range 10

  - 20.1.2.0/24 16005 range 1

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+----------------+----------+
| Parameter          | Description                                                                      | Range          | Default  |
+====================+==================================================================================+================+==========+
| prefix-sid-mapping | ip prefix                                                                        | | A.B.C.D/x    | \-       |
|                    |                                                                                  | | X:X::X:X/x   |          |
+--------------------+----------------------------------------------------------------------------------+----------------+----------+
| start-sid          | SID index value associated with prefix. The value must be interpreted in the     | 0-999999       | \-       |
|                    | context of value-type.                                                           |                |          |
+--------------------+----------------------------------------------------------------------------------+----------------+----------+
| range              | Describes how many SIDs could be allocated.                                      | 1-65535        | 1        |
+--------------------+----------------------------------------------------------------------------------+----------------+----------+
| s-flag             | control if s-flag is enabled (set) or disabled (unset) for the binding-sid tlv.  | | enabled      | disabled |
|                    | Enable s-flag to allow routers in the network to propagate binding-sids between  | | disabled     |          |
|                    | ISIS levels.                                                                     |                |          |
+--------------------+----------------------------------------------------------------------------------+----------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protםcols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# mapping-server
    dnRouter(cfg-sr-mpls-mapping)# prefix-sid-map 101.0.0.1/32 1000 range 100
    dnRouter(cfg-sr-mpls-mapping)# prefix-sid-map 101.0.2.1/32 10250 range 5
    dnRouter(cfg-sr-mpls-mapping)# prefix-sid-map 101.0.3.1/32 10300
    dnRouter(cfg-sr-mpls-mapping)# prefix-sid-map 101.0.4.1/32 10400 s-flag enabled

    dnRouter# configure
    dnRouter(cfg)# protםcols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# mapping-server
    dnRouter(cfg-sr-mpls-mapping)# prefix-sid-map 101::1/128 1000 range 100
    dnRouter(cfg-sr-mpls-mapping)# prefix-sid-map 101::2:1/128 10250 range 5
    dnRouter(cfg-sr-mpls-mapping)# prefix-sid-map 101::3:1/128 10300
    dnRouter(cfg-sr-mpls-mapping)# prefix-sid-map 101::4:1/128 10400 s-flag enabled


**Removing Configuration**

To remove prefix-mapping:
::

    dnRouter(cfg-sr-mpls-mapping)# no prefix-sid-map 101.0.0.1/32

**Command History**

+---------+-------------------------+
| Release | Modification            |
+=========+=========================+
| 15.0    | Command introduced      |
+---------+-------------------------+
| 18.3    | Add ipv6 prefix support |
+---------+-------------------------+
