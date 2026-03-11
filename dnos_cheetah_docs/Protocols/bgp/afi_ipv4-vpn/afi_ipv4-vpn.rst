protocols bgp address-family ipv4-vpn
-------------------------------------

**Minimum user role:** operator

To enter global BGP ipv4-VPN address-family configuration:

**Command syntax: address-family ipv4-vpn**

**Command mode:** config

**Hierarchies**

- protocols bgp

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-vpn
    dnRouter(cfg-protocols-bgp-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-protocols-bgp)# no address-family ipv4-vpn

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
