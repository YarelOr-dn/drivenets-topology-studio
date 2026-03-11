interfaces ipv4-address secondary
---------------------------------

**Minimum user role:** operator

This command assigns an IPv4 address for the interface being configured.

To configure the IPv4 address for an interface, use the following command:

**Command syntax: ipv4-address [ipv4-address] secondary**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**
- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan
  - IRB

- A primary address must be configured on the interface before attempting to add secondary addresses.

- Up to 19 secondary IPv4 addresses can be configured on an interface in addition to the primary IPv4 address.

- You cannot configure broadcast or subnet network address per subnet mask (the first and last address from /1 up to /30 masks).

- You cannot change or remove the IP address for an interface that is configured as the source-interface for another interface.

- You cannot configure both DHCP and a static IP address for the same interface. The last configuration applies.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter    | Description                                                                      | Range     | Default |
+==============+==================================================================================+===========+=========+
| ipv4-address | Configures a static IPv4 address for the interface. The subnet mask cannot be    | A.B.C.D/x | \-      |
|              | /0.                                                                              |           |         |
+--------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ipv4-address 1.2.3.4/22
    dnRouter(cfg-if-ge100-1/1/1)# ipv4-address 1.2.3.5/22 secondary

    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# ipv4-address 1.2.3.254/24

    dnRouter(cfg-if)# mgmt0
    dnRouter(cfg-if-mgmt0)# ipv4-address 1.2.3.4/24

    dnRouter(cfg-if)# gre-tunnel-0
    dnRouter(cfg-if-gre-0)# ipv4-address 10.10.10.0/31
    dnRouter(cfg-if-gre-0)# no ipv4-address


**Removing Configuration**

To remove the IPv4 address:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ipv4-address 10.10.10.0/31

To revert to default:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ipv4-address

**Command History**

+---------+--------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                             |
+=========+==========================================================================================================================+
| 5.1     | Command introduced                                                                                                       |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces; added option for unnumbered interface; applied new hierarchy; added         |
|         | restriction on /0 subnet mask                                                                                            |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Unnumbered interfaces not supported.                                                                                     |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 11.4    | Added support for GRE-tunnels                                                                                            |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 16.2    | Management bond interfaces removed                                                                                       |
+---------+--------------------------------------------------------------------------------------------------------------------------+
| 17.2    | Added support for secondary IPv4 addresses                                                                               |
+---------+--------------------------------------------------------------------------------------------------------------------------+
