protocols isis instance address-family ipv6-unicast segment-routing
-------------------------------------------------------------------

**Minimum user role:** operator

Enter isis segment-routing configuration level


**Command syntax: segment-routing**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)#


**Removing Configuration**

To revert all segment-routing configuration to default:
::

    dnRouter(cfg-isis-inst-afi)# no segment-routing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
