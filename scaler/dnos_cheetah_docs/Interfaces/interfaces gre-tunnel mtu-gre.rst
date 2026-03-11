interfaces mtu-gre
------------------

**Minimum user role:** operator

The maximum transmission unit (MTU) of a communication protocol of a layer defines the size of the largest protocol data unit that the layer is allowed to transmit over one interface. The MTU command configures L2 or L3 MTU for the interfaces. MTU is applicable to both control and datapath packets. The interface MTU affects only control traffic. Make sure that the MTU values are identical on all devices connected to the L2 network.
For GRE interfaces, the MTU is the payload size over the GRE tunnel (i.e without the IP & GRE header). By default, there is no fragmentation over the GRE tunnel. For the GRE interface, only MTU configuration is allowed. The GRE MTU is not counted as an MTU profile.

-	The sub-interface MTU must not be greater than the physical parent port MTU. The interface/sub-interface MTU must not be greater than max-hw-mtu (9300 for x86/QMX/J2 platforms).
-	NCP-40C and NCP-10CD support up to 8 different MTU configurations.

Each MTU profile configuration includes a unique tuple of all MTU types. For example:

-	MTU profile 0: (L2= 9000B, ipv4 = 8000B, ipv6 = 8000B, mpls = 8600B)
-	MTU profile 1: (L2= 9004B, ipv4 = 8000B, ipv6 = 8000B, mpls = 8600B)

The following table summarizes all available combinations in this version. x denotes the configured frame size.

+-------------+----------------+----------+--------------------------+
| Command     | Interface type | L2 frame | L3 frame                 |
+=============+================+==========+==========================+
+-------------+----------------+----------+--------------------------+
| mtu-gre x   | gre            |          | x                        |
|             |                |          |                          |
|             |                |          |                          |
+-------------+----------------+----------+--------------------------+

**Command syntax: mtu-gre [gre-mtu]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to gre-tunnel interfaces.

**Parameter table**

+-----------+--------------------------------+-----------+---------+
| Parameter | Description                    | Range     | Default |
+===========+================================+===========+=========+
| gre-mtu   | gre tunnel interface MTU value | 1500-9278 | 1500    |
+-----------+--------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# gre-tunnel-1
    dnRouter(cfg-if-gre-tunnel-1)# mtu-gre 5555


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-gre-tunnel-1)# no mtu-gre

**Command History**

+---------+---------------------------------------------------------------+
| Release | Modification                                                  |
+=========+===============================================================+
| 16.1    | Command introduced. Split from general interface MTU command. |
+---------+---------------------------------------------------------------+
| 16.2    | Command syntax renamed to mtu-gre                             |
+---------+---------------------------------------------------------------+
