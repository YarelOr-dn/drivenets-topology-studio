protocols bgp address-family ipv6-unicast
-----------------------------------------

**Minimum user role:** operator

To enter global BGP ipv6 address-family configuration:

**Command syntax: address-family ipv6-unicast**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-protocols-bgp)# no address-family ipv6-unicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
