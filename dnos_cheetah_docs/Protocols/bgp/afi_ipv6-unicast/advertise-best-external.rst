protocols bgp address-family ipv6-unicast advertise-best-external
-----------------------------------------------------------------

**Minimum user role:** operator

Allows advertising the best eBGP path to iBGP neighbors, even when the locally selected bestpath is from an iBGP neighbor.

Unicast routes maintain normal bgp behavior so that if the bestpath arrives from an iBGP neighbor, it will not be advertised to another iBGP neighbor.

When it is disabled, all best-external advertisements will be withdrawn.

To allow the device to receive multiple paths for the same route from the same BGP neighbor:

**Command syntax: advertise-best-external [advertise-best-external]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast

**Note**

- This command only supports Labeled-Unicast routes. 

**Parameter table**

+-------------------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter               | Description                                                                      | Range        | Default  |
+=========================+==================================================================================+==============+==========+
| advertise-best-external | Advertise the best eBGP path to iBGP neighbors, even when the locally selected   | | enabled    | disabled |
|                         | bestpath is from an iBGP neighbor                                                | | disabled   |          |
+-------------------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# advertise-best-external enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# advertise-best-external enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-bgp-afi)# no advertise-best-external

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.2    | Command introduced |
+---------+--------------------+
