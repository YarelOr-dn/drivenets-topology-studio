interfaces mtu
--------------

**Minimum user role:** operator

The maximum transmission unit (MTU) of a communication protocol of a layer defines the size of the largest protocol data unit that the layer is allowed to transmit over one interface. The MTU command configures L2 or L3 MTU for the interfaces. MTU is applicable to both control and datapath packets. The interface MTU affects only control traffic. Make sure that the MTU values are identical on all devices connected to the L2 network.

-	The sub-interface MTU must not be greater than the physical parent port MTU. The interface/sub-interface MTU must not be greater than max-hw-mtu (9300 for x86/QMX/J2 platforms).
-	NCP-40C and NCP-10CD support up to 8 different MTU configurations.
-	MPLS MTU assumes 2 MPLS labels (the labels included in the MTU calculation)

Each MTU profile configuration includes a unique tuple of all MTU types. For example:

-	MTU profile 0: (L2= 9000B, ipv4 = 8000B, ipv6 = 8000B, mpls = 8600B)
-	MTU profile 1: (L2= 9004B, ipv4 = 8000B, ipv6 = 8000B, mpls = 8600B)

The following table summarizes all available combinations in this version. x denotes the configured frame size.

+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| Command     | Interface type | L2 frame | L3 frame                 | Validated range                                                     |
+=============+================+==========+==========================+=====================================================================+
| mtu x       | untagged       | x        | x - 14                   | -  <1514 - Max_HW_MTU> if there are no sub interfaces under it      |
|             |                |          |                          |                                                                     |
|             |                |          | for MPLS and other types | -  <1514 - (Max_HW_MTU-4)> if there is .1Q interface under it       |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1514 - (Max_HW_MTU-8)> if there is QinQ interface under it      |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu x       | .1q            | x        | x - 18                   | -  <1518 - Max_HW_MTU> if there is no QinQ interface on parent      |
|             |                |          |                          |                                                                     |
|             |                |          | for MPLS and other types | -  <1518 - (Max_HW_MTU-4)> if there is QinQ interface on parent     |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu x       | qinq           | x        | x - 22                   | -  <1522 - Max_HW_MTU>                                              |
|             |                |          |                          |                                                                     |
|             |                |          | for MPLS and other types |                                                                     |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu ipv4 x  | untagged       |          | x for ipv4               | -  <1500 - (Max_HW_MTU-14)> if there are no sub interfaces under it |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1500 - (Max_HW_MTU-18)> if there is .1Q interface under it      |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1500 - (Max_HW_MTU-22)> if there is QinQ interface under it     |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu ipv4 x  | .1q            |          | x for ipv4               | -  <1500 - (Max_HW_MTU-18)> if there is no QinQ interface on parent |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1500 - (Max_HW_MTU-22)> if there is QinQ interface on parent    |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu ipv4 x  | qinq           |          | x for ipv4               | -  <1500 - (Max_HW_MTU-22)>                                         |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu ipv6 x  | untagged       |          | x for ipv6               | -  <1500 - (Max_HW_MTU-14)> if there are no sub interfaces under it |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1500 - (Max_HW_MTU-18)> if there is .1Q interface under it      |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1500 - (Max_HW_MTU-22)> if there is QinQ interface under it     |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu ipv6 x  | .1q            |          | x for ipv6               | -  <1500 - (Max_HW_MTU-18)> if there is no QinQ interface on parent |
|             |                |          |                          |                                                                     |
|             |                |          |                          | <1500 - (Max_HW_MTU-22)> if there is QinQ interface on parent       |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu ipv6 x  | qinq           |          | x for ipv6               | -  <1500 - (Max_HW_MTU-22)>                                         |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu mpls x  | untagged       |          | x for mpls               | -  <1508 - (Max_HW_MTU-14)> if there are no sub interfaces under it |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1508 - (Max_HW_MTU-18)> if there is .1Q interface under it      |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1508 - (Max_HW_MTU-22)> if there is QinQ interface under it     |
|             |                |          |                          |                                                                     |
|             |                |          |                          |                                                                     |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu mpls x  | .1q            |          | x for mpls               | -  <1508 - (Max_HW_MTU-18)> if there is no QinQ interface on parent |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1508 - (Max_HW_MTU-22)> if there is QinQ interface on parent    |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu mpls x  | qinq           |          | x for mpls               | -  <1508 - (Max_HW_MTU-22)>                                         |
|             |                |          |                          |                                                                     |
|             |                |          |                          |                                                                     |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+

You can limit the allowed size of control packets going through an interface with the following command:

**Command syntax: mtu** [mtu] mtu-ipv4 [mtu-ipv4] mtu-ipv6 [mtu-ipv6] mtu-mpls [mtu-mpls]

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:
	- Physical
	- Physical vlan
	- Bundle
	- Bundle vlan
	- mgmt0


**Parameter table**

+---------------+------------------------------------------------------------------------------+------------------------+-------------+
|               |                                                                              |                        |             |
| Parameter     | Description                                                                  | Range                  | Default     |
+===============+==============================================================================+========================+=============+
|               |                                                                              |                        |             |
| mtu           | The maximum packet size for all packets that go   through the interface.     | 1514..max_hw_mtu       | 1514        |
+---------------+------------------------------------------------------------------------------+------------------------+-------------+
|               |                                                                              |                        |             |
| mtu-ipv4      | The maximum packet size for IPv4 packets that go   through the interface.    | 1500..max_hw_mtu-14    | 1500        |
+---------------+------------------------------------------------------------------------------+------------------------+-------------+
|               |                                                                              |                        |             |
| mtu-ipv6      | The maximum packet size for IPv6 packets that go   through the interface.    | 1500..max_hw_mtu-14    | 1500        |
+---------------+------------------------------------------------------------------------------+------------------------+-------------+
|               |                                                                              |                        |             |
| mtu-mpls      | The maximum packet size for MPLS packets that go   through the interface.    | 1508..max_hw_mtu-14    | 1500        |
+---------------+------------------------------------------------------------------------------+------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	
	dnRouter(cfg-if)# bundle-1
	dnRouter(cfg-if-bundle-1)# mtu 1514
	
	dnRouter(cfg-if)# bundle-1.100
	dnRouter(cfg-if-bundle-1.100)# mtu 1514
	
	dnRouter(cfg-if)# ge10-2/1/1.100
	dnRouter(cfg-if-ge10-2/1/1.100)# mtu 9000


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-if-bundle-1.100)# no mtu


.. **Help line:** Configure interface mtu

**Command History**

+-------------+-----------------------------------------------------------------------------------+
|             |                                                                                   |
| Release     | Modification                                                                      |
+=============+===================================================================================+
|             |                                                                                   |
| 5.1.0       | Command introduced                                                                |
+-------------+-----------------------------------------------------------------------------------+
|             |                                                                                   |
| 6.0         | Changed syntax from interface to interfaces,   added address family, removed mpls |
|             |                                                                                   |
|             | Applied new hierarchy                                                             |
+-------------+-----------------------------------------------------------------------------------+
|             |                                                                                   |
| 9.0         | Removed MTU configuration per address-family                                      |
+-------------+-----------------------------------------------------------------------------------+
|             |                                                                                   |
| 11.0        | Added option to configure separately for IPv4,   IPv6 and MPLS                    |
+-------------+-----------------------------------------------------------------------------------+
|             |                                                                                   |
| 11.4        | Added support for GRE-tunnels                                                     |
+-------------+-----------------------------------------------------------------------------------+
