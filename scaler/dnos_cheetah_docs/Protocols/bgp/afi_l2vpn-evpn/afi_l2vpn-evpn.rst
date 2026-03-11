protocols bgp address-family l2vpn-evpn
---------------------------------------

**Minimum user role:** operator

To enter global BGP l2vpn-evpn address-family configuration:

**Command syntax: address-family l2vpn-evpn**

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
    dnRouter(cfg-protocols-bgp)# address-family l2vpn-evpn
    dnRouter(cfg-protocols-bgp-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-protocols-bgp)# no address-family l2vpn-evpn

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
