protocols isis instance address-family ipv4-unicast segment-routing
-------------------------------------------------------------------

**Minimum user role:** operator

To enter the isis segment-routing configuration level:


**Command syntax: segment-routing**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)#


**Removing Configuration**

To revert all segment-routing configurations to the default value:
::

    dnRouter(cfg-isis-inst-afi)# no segment-routing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
