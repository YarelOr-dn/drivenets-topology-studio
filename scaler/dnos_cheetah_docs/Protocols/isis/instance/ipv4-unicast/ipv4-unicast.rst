protocols isis instance address-family ipv4-unicast
---------------------------------------------------

**Minimum user role:** operator

The enter the isis address-family ipv4 unicast configuration:

**Command syntax: address-family ipv4-unicast**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- The configuration within this address-family only takes effect once the topology is enabled.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)#


**Removing Configuration**

To revert all ipv4 unicast configuration to default:
::

    dnRouter(cfg-protocols-isis-inst)# no address-family ipv4-unicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
