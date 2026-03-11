protocols bgp address-family ipv6-unicast add-path receive
----------------------------------------------------------

**Minimum user role:** operator

Typically, BGP routers advertise only the best path for each route. The advertisement of a prefix replaces the previous announcement of that prefix.

To allow the device to receive multiple paths for the same route from the same BGP neighbor:

**Command syntax: add-path receive [add-path-receive]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv4-multicast
- protocols bgp address-family ipv4-vpn
- protocols bgp address-family ipv6-vpn

**Note**

- This command is only applicable to unicast, VPN and multicast sub-address-families.

- This command is only applicable to the default VRF.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter        | Description                                                                      | Range        | Default  |
+==================+==================================================================================+==============+==========+
| add-path-receive | Enables additional paths to be received for the same route from a bgp neighbor.  | | enabled    | disabled |
|                  | Applies for all bgp neighbors with this afi/safi                                 | | disabled   |          |
+------------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path receive enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path receive enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-bgp-afi)# no add-path receive

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 9.0     | Command introduced                                  |
+---------+-----------------------------------------------------+
| 16.1    | Extended command to support BGP IPv4 multicast SAFI |
+---------+-----------------------------------------------------+
