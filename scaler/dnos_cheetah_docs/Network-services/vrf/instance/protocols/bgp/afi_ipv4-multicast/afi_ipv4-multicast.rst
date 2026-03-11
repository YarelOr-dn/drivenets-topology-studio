network-services vrf instance protocols bgp address-family ipv4-multicast
-------------------------------------------------------------------------

**Minimum user role:** operator

To enter the global BGP ipv4 multicast address-family configuration:

**Command syntax: address-family ipv4-multicast**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-multicast
    dnRouter(cfg-protocols-bgp-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-protocols-bgp)# no address-family ipv4-multicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
