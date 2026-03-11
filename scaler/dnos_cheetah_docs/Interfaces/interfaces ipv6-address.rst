interfaces ipv6-address
-----------------------

**Minimum user role:** operator

To configure the IPv6 address for an interface, use the following command:

**Command syntax: ipv6-address [ipv6-address]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan
  - Loopback
  - mgmt0
  - IRB

- Loopback interfaces can be configured with /128 address only.

- You cannot configure both DHCPv6 and a static IP address for the same interface. The last configuration applies.

**Parameter table**

+--------------+-----------------------------------------------------+------------+---------+
| Parameter    | Description                                         | Range      | Default |
+==============+=====================================================+============+=========+
| ipv6-address | Configures a static IPv6 address for the interface. | X:X::X:X/x | \-      |
+--------------+-----------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ipv6-address 2001:ab12::1/127


**Removing Configuration**

To remove the IPv6 address:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ipv6-address

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces; applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 16.2    | Management bond interfaces removed                                 |
+---------+--------------------------------------------------------------------+
