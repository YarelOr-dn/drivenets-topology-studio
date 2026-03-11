interfaces ipv6-admin-state
---------------------------

**Minimum user role:** operator

By default, all IPv6-enabled interfaces have a link-local unicast address. For network interfaces, the link-local address will be generated when (1) IPv6 admin-state is enabled; and (2) a global unicast address is configured on the interface. When the IPv6 admin-state is disabled or if the global unicast address is not configured on the interface, there will be no link-local address and the IPv6 global address will not be used (regardless if a global ipv6-address has been configured).

To enable/disable IPv6 on an interface, use the following command:

**Command syntax: ipv6-admin-state [admin-state]**

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

**Parameter table**

+-------------+---------------------------------------------------------+--------------+---------+
| Parameter   | Description                                             | Range        | Default |
+=============+=========================================================+==============+=========+
| admin-state | Sets the administrative state of IPv6 on the interface. | | enabled    | enabled |
|             |                                                         | | disabled   |         |
+-------------+---------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# ipv6-admin-state enabled
    dnRouter(cfg-if-ge100-0/0/0)# ipv6-admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge100-0/0/0)# no ipv6-admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
