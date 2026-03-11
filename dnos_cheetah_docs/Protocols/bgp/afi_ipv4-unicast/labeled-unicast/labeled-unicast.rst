protocols bgp address-family ipv4-unicast labeled-unicast
---------------------------------------------------------

**Minimum user role:** operator

To enter labled-unicast safi configuration level:

**Command syntax: labeled-unicast**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# labeled-unicast
    dnRouter(cfg-bgp-afi-lu)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# labeled-unicast
    dnRouter(cfg-bgp-afi-lu)#


**Removing Configuration**

To remove the labled-unicast configuration:
::

    dnRouter(cfg-protocols-bgp-afi)# no labeled-unicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
