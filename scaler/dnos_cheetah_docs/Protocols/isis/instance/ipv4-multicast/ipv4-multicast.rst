protocols isis instance address-family ipv4-multicast
-----------------------------------------------------

**Minimum user role:** operator

Enter the isis address-family ipv4 multicast configuration level:

**Command syntax: address-family ipv4-multicast**

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
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)#


**Removing Configuration**

To revert all ipv4 multicast configuration to default:
::

    dnRouter(cfg-protocols-isis-inst)# no address-family ipv4-multicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
