protocols isis instance address-family ipv6-unicast segment-routing mapping-server
----------------------------------------------------------------------------------

**Minimum user role:** operator

A mapping-server with advertise enabled advertises the binding SIDs defined in "segment-routing mpls mapping-server prefix-sid-map". A mapping-server with receive enabled is a mapping-client and accepts binding SIDs as if there were prefix-SID advertised from network nodes. See "isis instance address-family segment-routing mapping-server prefix-sid-map advertise" and "isis instance address-family segment-routing mapping-server prefix-sid-map receive".

To configure the segment routing mapping server:

**Command syntax: mapping-server**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast segment-routing

**Note**

- Configuration of an IPv6-unicast mapping-server applies for IPv6 binding-sid handling regardless of topology.

- -In case of a single topology, the IPv6 binding-SIDs are advertised and honored under TLV 149.

- -In case of a multi topology, the IPv6 binding-SIDs are advertised and honored under TLV 150.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)# mapping-server
    dnRouter(cfg-afi-sr-mapping)#


**Removing Configuration**

To revert all mapping-server configuration to their default values:
::

    dnRouter(cfg-inst-afi-sr)# no mapping-server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
