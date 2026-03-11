interfaces mtu-mpls
-------------------

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
| mtu-mpls x  | untagged       |          | x for mpls               | -  <1280 - (Max_HW_MTU-14)> if there are no sub interfaces under it |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1280 - (Max_HW_MTU-18)> if there is .1Q interface under it      |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1280 - (Max_HW_MTU-22)> if there is QinQ interface under it     |
|             |                |          |                          |                                                                     |
|             |                |          |                          |                                                                     |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu-mpls x  | .1q            |          | x for mpls               | -  <1280 - (Max_HW_MTU-18)> if there is no QinQ interface on parent |
|             |                |          |                          |                                                                     |
|             |                |          |                          | -  <1280 - (Max_HW_MTU-22)> if there is QinQ interface on parent    |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+
| mtu-mpls x  | qinq           |          | x for mpls               | -  <1280 - (Max_HW_MTU-22)>                                         |
|             |                |          |                          |                                                                     |
|             |                |          |                          |                                                                     |
+-------------+----------------+----------+--------------------------+---------------------------------------------------------------------+

**Command syntax: mtu-mpls [mpls-mtu]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

The command is applicable to the following interface types:

- Physical
- Physical vlan
- Bundle
- Bundle vlan
- IRB

**Parameter table**

+-----------+----------------------------------+-----------+---------+
| Parameter | Description                      | Range     | Default |
+===========+==================================+===========+=========+
| mpls-mtu  | MPLS MTU value of the interface. | 1280-9286 | \-      |
+-----------+----------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces

    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# mtu-mpls 1514

    dnRouter(cfg-if)# bundle-1.100
    dnRouter(cfg-if-bundle-1.100)# mtu-mpls 1514

    dnRouter(cfg-if)# ge10-2/1/1.100
    dnRouter(cfg-if-ge10-2/1/1.100)# mtu-mpls 9000


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1.100)# no mtu-mpls

**Command History**

+---------+---------------------------------------------------------------+
| Release | Modification                                                  |
+=========+===============================================================+
| 16.1    | Command introduced. Split from general interface MTU command. |
+---------+---------------------------------------------------------------+
| 18.3    | Extended the supported MTU range.                             |
+---------+---------------------------------------------------------------+
