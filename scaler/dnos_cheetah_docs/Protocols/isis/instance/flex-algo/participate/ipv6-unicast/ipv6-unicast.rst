protocols isis instance flex-algo participate address-family ipv6-unicast
-------------------------------------------------------------------------

**Minimum user role:** operator

The enter the isis address-family ipv6 unicast configuration:

**Command syntax: address-family ipv6-unicast**

**Command mode:** config

**Hierarchies**

- protocols isis instance flex-algo participate

**Note**

- The configuration within this address-family only takes effect once the topology is enabled.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# flex-algo
    dnRouter(cfg-isis-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)# address-family ipv6-unicast
    dnRouter(cfg-flex-algo-participate-afi)#


**Removing Configuration**

To revert all ipv6 unicast configuration to default:
::

    dnRouter(cfg-flex-algo-participate)# no address-family ipv6-unicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
