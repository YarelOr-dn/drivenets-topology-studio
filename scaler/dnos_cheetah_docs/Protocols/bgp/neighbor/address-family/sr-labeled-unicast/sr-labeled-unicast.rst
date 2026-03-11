protocols bgp neighbor address-family sr-labeled-unicast
--------------------------------------------------------

**Minimum user role:** operator

To enter sr-labeled-unicast configuration level.
Configuration in this level will only have affect if the ipv4/ipv6-unicast address-family is set to work in the labeled-unicast safi mode (safi 4).

**Command syntax: sr-labeled-unicast**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family

**Note**

- Notice the change in prompt.

- Valid only for the default vrf.

- Supported for both the neighbor and peer group. Not supported for the neighbor within the peer group.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# sr-labeled-unicast
    dnRouter(cfg-neighbor-afi-sr-lu)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# sr-labeled-unicast
    dnRouter(cfg-group-afi-sr-lu)#


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
