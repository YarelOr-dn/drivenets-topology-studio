protocols isis instance address-family ipv6-unicast
---------------------------------------------------

**Minimum user role:** operator

To enter the ISIS address-family ipv6 unicast configuration:

**Command syntax: address-family ipv6-unicast**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- The configuration within this address-family only takes effect once the topology is enabled.

- Traffic Engineering extensions are now supported on ISIS IPv6-Unicast topology.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)#


**Removing Configuration**

To revert all ipv6 unicast configuration to default:
::

    dnRouter(cfg-protocols-isis-inst)# no address-family ipv6-unicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
